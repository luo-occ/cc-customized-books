from __future__ import annotations

from dataclasses import dataclass
import posixpath
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from bs4 import BeautifulSoup


CONTAINER_PATH = "META-INF/container.xml"
CONTAINER_NAMESPACES = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
}
OPF_NAMESPACES = {"opf": "http://www.idpf.org/2007/opf"}
NCX_NAMESPACES = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}
XHTML_MEDIA_TYPE = "application/xhtml+xml"
NCX_MEDIA_TYPE = "application/x-dtbncx+xml"
IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
COVER_HINTS = ("cover", "cover-image", "front-cover", "titlepage")


@dataclass(frozen=True)
class NavEntry:
    label: str
    href: str


@dataclass(frozen=True)
class EpubStructure:
    opf_path: str
    spine: list[str]
    nav: list[NavEntry]

    @property
    def spine_hrefs(self) -> list[str]:
        return self.spine

    @property
    def nav_entries(self) -> list[NavEntry]:
        return self.nav


@dataclass(frozen=True)
class CoverAsset:
    href: str
    media_type: str
    content: bytes


def read_container_path(zf: ZipFile) -> str:
    container_xml = zf.read(CONTAINER_PATH)
    root = ET.fromstring(container_xml)
    rootfile = root.find(
        "container:rootfiles/container:rootfile", CONTAINER_NAMESPACES
    )
    if rootfile is None or "full-path" not in rootfile.attrib:
        raise ValueError("container.xml does not define a rootfile full-path")
    return rootfile.attrib["full-path"]


def load_epub_structure(epub_path: str | Path) -> EpubStructure:
    epub_path = Path(epub_path)
    with ZipFile(epub_path) as zf:
        opf_path = read_container_path(zf)
        opf_root = ET.fromstring(zf.read(opf_path))
        opf_dir = posixpath.dirname(opf_path)
        manifest = _load_manifest(opf_root, opf_dir)

        spine = opf_root.find("opf:spine", OPF_NAMESPACES)
        if spine is None:
            raise ValueError("OPF spine is missing")

        spine_hrefs = []
        for itemref in spine.findall("opf:itemref", OPF_NAMESPACES):
            item = manifest.get(itemref.attrib.get("idref", ""))
            if item and item["media_type"] == XHTML_MEDIA_TYPE:
                spine_hrefs.append(item["href"])

        nav_entries = []
        ncx_path = _find_ncx_path(spine, manifest)
        if ncx_path is not None:
            nav_entries = _load_ncx_entries(zf, ncx_path)

    return EpubStructure(opf_path=opf_path, spine=spine_hrefs, nav=nav_entries)


def extract_cover_asset(epub_path: str | Path) -> CoverAsset | None:
    epub_path = Path(epub_path)
    with ZipFile(epub_path) as zf:
        opf_path = read_container_path(zf)
        opf_root = ET.fromstring(zf.read(opf_path))
        opf_dir = posixpath.dirname(opf_path)
        manifest = _load_manifest(opf_root, opf_dir)

        explicit_cover_id = _find_metadata_cover_id(opf_root)
        if explicit_cover_id:
            cover = _cover_from_manifest(zf, manifest, explicit_cover_id)
            if cover is not None:
                return cover

        for item_id, item in manifest.items():
            if "cover-image" in _item_properties(item):
                cover = _cover_from_manifest(zf, manifest, item_id)
                if cover is not None:
                    return cover

        heuristic_cover = _find_cover_like_manifest_item(zf, manifest)
        if heuristic_cover is not None:
            return heuristic_cover

        spine = opf_root.find("opf:spine", OPF_NAMESPACES)
        if spine is not None:
            return _find_frontmatter_cover(zf, manifest, spine)

    return None


def clean_body_fragment(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    body = soup.body or soup

    for tag in body.find_all(["script", "style"]):
        tag.decompose()

    for tag in body.find_all(True):
        allowed_attrs = _allowed_attrs(tag.name)
        for attr_name in list(tag.attrs):
            if attr_name not in allowed_attrs:
                del tag.attrs[attr_name]

    return "".join(str(node) for node in body.contents).strip()


def extract_href_fragment(epub_path: str | Path, href: str) -> str:
    epub_path = Path(epub_path)
    path_part, _, fragment_id = href.partition("#")

    with ZipFile(epub_path) as zf:
        opf_path = read_container_path(zf)
        content_path = _resolve_opf_href(posixpath.dirname(opf_path), path_part)
        raw = zf.read(content_path).decode("utf-8")

    soup = BeautifulSoup(raw, "html.parser")
    body = soup.body or soup
    if fragment_id:
        target = body.find(id=fragment_id)
        if target is None:
            raise ValueError(f"Fragment '{fragment_id}' not found in {content_path}")

        section = _nearest_body_child(body, target)
        nodes = [section, *section.next_siblings]
        return clean_body_fragment("".join(str(node) for node in nodes))
    return clean_body_fragment(str(body))


def _resolve_opf_href(opf_dir: str, href: str) -> str:
    if not opf_dir:
        return posixpath.normpath(href)
    return posixpath.normpath(posixpath.join(opf_dir, href))


def _load_manifest(
    opf_root: ET.Element, opf_dir: str
) -> dict[str, dict[str, str | set[str]]]:
    manifest: dict[str, dict[str, str | set[str]]] = {}
    for item in opf_root.findall("opf:manifest/opf:item", OPF_NAMESPACES):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        if not item_id or not href:
            continue
        manifest[item_id] = {
            "href": _resolve_opf_href(opf_dir, href),
            "media_type": item.attrib.get("media-type", ""),
            "properties": set(item.attrib.get("properties", "").split()),
        }
    return manifest


def _find_metadata_cover_id(opf_root: ET.Element) -> str | None:
    metadata = opf_root.find("opf:metadata", OPF_NAMESPACES)
    if metadata is None:
        return None

    for node in metadata.findall("opf:meta", OPF_NAMESPACES):
        if node.attrib.get("name") == "cover":
            return node.attrib.get("content")
    return None


def _cover_from_manifest(
    zf: ZipFile,
    manifest: dict[str, dict[str, str | set[str]]],
    item_id: str,
) -> CoverAsset | None:
    item = manifest.get(item_id)
    if item is None:
        return None

    media_type = _item_media_type(item)
    if media_type not in IMAGE_MEDIA_TYPES:
        return None

    href = _item_href(item)
    return CoverAsset(href=href, media_type=media_type, content=zf.read(href))


def _find_cover_like_manifest_item(
    zf: ZipFile, manifest: dict[str, dict[str, str | set[str]]]
) -> CoverAsset | None:
    for item_id, item in manifest.items():
        media_type = _item_media_type(item)
        if media_type not in IMAGE_MEDIA_TYPES:
            continue
        if _is_cover_like(item_id, _item_href(item)):
            return _cover_from_manifest(zf, manifest, item_id)
    return None


def _find_frontmatter_cover(
    zf: ZipFile,
    manifest: dict[str, dict[str, str | set[str]]],
    spine: ET.Element,
) -> CoverAsset | None:
    itemrefs = spine.findall("opf:itemref", OPF_NAMESPACES)
    for itemref in itemrefs[:3]:
        content_item = manifest.get(itemref.attrib.get("idref", ""))
        if content_item is None:
            continue
        if _item_media_type(content_item) != XHTML_MEDIA_TYPE:
            continue

        content_href = _item_href(content_item)
        soup = BeautifulSoup(zf.read(content_href).decode("utf-8"), "html.parser")
        for image in soup.find_all("img"):
            src = image.get("src", "").strip()
            if not src:
                continue
            image_href = _resolve_relative_href(posixpath.dirname(content_href), src)
            cover = _cover_from_href(zf, manifest, image_href)
            if cover is not None:
                return cover
    return None


def _cover_from_href(
    zf: ZipFile,
    manifest: dict[str, dict[str, str | set[str]]],
    href: str,
) -> CoverAsset | None:
    for item in manifest.values():
        if _item_href(item) != href:
            continue
        media_type = _item_media_type(item)
        if media_type not in IMAGE_MEDIA_TYPES:
            return None
        return CoverAsset(href=href, media_type=media_type, content=zf.read(href))
    return None


def _is_cover_like(item_id: str, href: str) -> bool:
    haystack = f"{item_id} {posixpath.basename(href)}".lower()
    return any(hint in haystack for hint in COVER_HINTS)


def _item_href(item: dict[str, str | set[str]]) -> str:
    return str(item["href"])


def _item_media_type(item: dict[str, str | set[str]]) -> str:
    return str(item["media_type"])


def _item_properties(item: dict[str, str | set[str]]) -> set[str]:
    properties = item.get("properties", set())
    return properties if isinstance(properties, set) else set()


def _find_ncx_path(
    spine: ET.Element, manifest: dict[str, dict[str, str | set[str]]]
) -> str | None:
    toc_id = spine.attrib.get("toc")
    if toc_id:
        item = manifest.get(toc_id)
        if item is not None:
            return _item_href(item)

    for item in manifest.values():
        if _item_media_type(item) == NCX_MEDIA_TYPE:
            return _item_href(item)
    return None


def _load_ncx_entries(zf: ZipFile, ncx_path: str) -> list[NavEntry]:
    root = ET.fromstring(zf.read(ncx_path))
    nav_map = root.find("ncx:navMap", NCX_NAMESPACES)
    if nav_map is None:
        return []

    ncx_dir = posixpath.dirname(ncx_path)
    entries: list[NavEntry] = []
    for nav_point in nav_map.findall("ncx:navPoint", NCX_NAMESPACES):
        _append_nav_point(entries, nav_point, ncx_dir)
    return entries


def _append_nav_point(
    entries: list[NavEntry], nav_point: ET.Element, ncx_dir: str
) -> None:
    label_node = nav_point.find("ncx:navLabel/ncx:text", NCX_NAMESPACES)
    content_node = nav_point.find("ncx:content", NCX_NAMESPACES)
    label = "" if label_node is None or label_node.text is None else label_node.text.strip()
    href = ""
    if content_node is not None:
        href = _resolve_relative_href(
            ncx_dir, _strip_fragment(content_node.attrib.get("src", "").strip())
        )
    if label or href:
        entries.append(NavEntry(label=label, href=href))

    for child in nav_point.findall("ncx:navPoint", NCX_NAMESPACES):
        _append_nav_point(entries, child, ncx_dir)


def _nearest_body_child(body: BeautifulSoup, target):
    node = target
    while getattr(node, "parent", None) is not body:
        parent = getattr(node, "parent", None)
        if parent is None:
            raise ValueError("Fragment target is not inside the document body")
        node = parent
    return node


def _resolve_relative_href(base_dir: str, href: str) -> str:
    if not href:
        return ""
    if not base_dir:
        return posixpath.normpath(href)
    return posixpath.normpath(posixpath.join(base_dir, href))


def _strip_fragment(href: str) -> str:
    return href.split("#", 1)[0]


def _allowed_attrs(tag_name: str) -> set[str]:
    allowed = {"id"}
    if tag_name == "a":
        return allowed | {"href"}
    if tag_name == "img":
        return allowed | {"src", "alt"}
    return allowed
