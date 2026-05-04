# Teacher-Mode Book Companion Refinement

## Goal

Upgrade the customized book companion from a helpful reading aid into a stronger teaching layer.

The user wants more than clear background and summary. They want sharper interpretation, stronger ideas, more serious questions, and better awareness of blind spots and competing views. The companion should feel less like a passive guide and more like a strong class taught by someone who understands the subject deeply.

## Core Teacher Mode

Default behavior should shift to a layered teacher mode.

The companion should combine three strengths:

1. **Interpretive and opinionated**
   Lead with a strong thesis about what the book or chapter is really doing.

2. **Aware of blind spots and rival views**
   Name the most important limits, omissions, or competing interpretations when they matter.

3. **Question-driven**
   End with a few sharp questions that help the reader test the interpretation against the text.

This should not become vague, academic, or overlong. The goal is sharper reading, not just more commentary.

## Book-Level Teacher Structure

Every book should receive a teacher-level introduction.

That introduction should include:

1. **Central thesis**
   What the book is fundamentally about beyond its surface subject or plot.

2. **Why this book matters**
   Why it still deserves attention and what kind of intellectual or human problem it opens.

3. **Historical / philosophical / political / technical frame**
   The larger frame needed to read the book intelligently.

4. **Strong interpretation**
   The main teaching view of the book.

5. **Blind spots and competing views**
   The most important objections, alternate readings, or limits.

6. **What to watch while reading**
   The tensions, patterns, concepts, or narrative structures worth tracking.

7. **Sharp questions**
   A few serious questions that make the reading active rather than passive.

This should feel like the opening of a serious class, not a neutral encyclopedia entry and not a bloated background memo.

## Chapter-Level Teacher Structure

Every chapter should still be guided, but only key chapters should receive full deep analysis by default.

### Normal Chapters

Normal chapters should still include:

- what happens or what is argued
- why it matters
- what to pay attention to

### Key Chapters

Key chapters should receive a compact **mini lecture**.

A key chapter is one that is either:

- a major turning point, or
- unusually rich in thematic or intellectual density

The mini lecture should include:

1. **Chapter thesis**
   What this chapter really accomplishes.

2. **Why it is pivotal**
   What changes here in plot, argument, or conceptual structure.

3. **Deeper interpretation**
   The strongest reading of what is happening under the surface.

4. **Blind spots / rival readings**
   The most useful challenge to that interpretation.

5. **Questions to carry**
   A few sharp questions before or after reading/listening.

This should be deeper than ordinary chapter notes, but still compact enough to fit a listening-oriented flow.

## Book-Type Adaptation

Teacher mode should adjust its depth and emphasis based on the kind of book.

### Fiction / Literature

Focus on:

- structure
- symbols
- moral tension
- psychology
- politics
- narrative voice
- what the work reveals about human life

Avoid flat plot retelling. The analysis should ask what the work is doing through form, pattern, and tension.

### History / Biography / Politics

Focus on:

- argument
- evidence
- framing
- interpretation of events
- omissions
- ideology
- how the author guides judgment

The companion should identify where the book is strongest, narrowest, or most contestable.

### Philosophy / Social Thought / Theory

Focus on:

- the main claim
- internal logic
- assumptions
- tensions
- likely objections
- what follows if the argument is right

The companion should distinguish clearly between what the author proves, assumes, and implies.

### Technical / Knowledge Books

Focus on:

- the core model
- the practical insight
- hidden assumptions
- community disagreement
- where the book is ahead of or behind current understanding
- what is genuinely useful versus secondary

The companion should separate essentials from optional technical detail.

## Output Behavior

Teacher mode should strengthen insight, not create listening clutter.

That means:

- keep the listening-friendly structure already established
- use sharper claims, not more filler
- keep rival views selective and high-value
- use questions to activate thought, not pad the output

The result should feel more demanding and more rewarding, while still being listenable.

## Process Changes

### Content Contract

`companion.json` should support stronger teaching fields where needed, including:

- book thesis
- strong interpretation
- blind spots / competing views
- sharp questions
- key-chapter marker
- key-chapter mini-lecture content

### Renderer

The renderer should present this material clearly without making it sound academic, overloaded, or noisy when heard aloud.

### Agent Guide

`AGENTS.md` should explicitly tell future agents to act more like a subject teacher:

- make stronger claims
- provide deeper context
- include selective rival views
- ask sharper questions
- vary depth by book type

### Per-Book Migration

Existing books such as *Animal Farm* should be upgraded from a competent companion to a teacher-mode companion.

## Success Criteria

The refinement is successful when:

1. Book introductions feel intellectually sharper
2. Key chapters receive stronger interpretive mini lectures
3. The companion helps the user think, not just understand
4. Rival views and blind spots are present where useful without overwhelming the reading
5. The tone feels like being taught by a serious subject teacher rather than reading a generic study aid
