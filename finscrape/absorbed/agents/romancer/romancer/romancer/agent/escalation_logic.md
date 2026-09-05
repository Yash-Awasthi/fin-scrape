# ROMANCER Escalation Ladder Logic

## Introduction

ROMANCER Escalation Ladders have some simple but non-obvious logic in terms of how they behave in ROMANCER. This document aims to cover that logic.

This document assumes that the reader is familiar with Herman Kahn's Escalation Ladder, from his 1965 book "On Escalation".  

## Definions and Preparation

An escalation ladder is an ego-centric view, and each actor has their own.

At any moment, an actor thinks of themselves as being at some specific rung, on that ladder. Rungs on the ladder are ordered.

Each actor has an event queue, that includes "time event happens" and "details of the event". As time progresses, events happen at their appointed times.

Each rung on the ladder has three things associated with it:
* Matching Rules
* Escalation Actions
* De-escalation Actions

## Logic

As events roll in the scenario, each actor re-evaluates the ladder and picks a rung:
1. If the Amygdala is dominant in decision making [ie, the PBF level is above the threshold], then a rung is chosen based on current dominant reflex behaviour:
   1. "Fight": the chosen rung is one above the current rung.
   1. "Freeze": the chosen rung is the same as the current one.
   1. "Flight": the chosen rung is the one below the current rung.
1. If the Amygdala is not dominant, then:
   1. All rungs on the ladder are matched against the current scenario, using each rung's matching rules.
   1. The highest-level rung that positively matched is chosen.

Next, rungs and behaviours occur according to this logic:
1. If the chosen rung is the same as the current rung:
   1. No changes or actions ensue
   1. A dummy event is put in the queue to trigger re-evaluation of this reasoner logic.
1. If the chosen rung is higher than the current rung:
   1. All of the "Escalation Actions" associated with this higher rung are added to the event queue.
   1. Add an event to the event queue that will move the agent to the new rung.
1. If the chosen rung is lower than the current rung:
   1. If the amydala forced the issue using the "flight" reflex:
      1. All of the "De-escalation Actions" for the current rung are put into the queue
   1. If the new rung was chosen by rung matching rules
      1. Add an event to the event queue that will move the agent to the new rung.

## On Case Based Reasoners and Escalation Ladders

All of the material described above is for the classic "Escalation Ladder Reasoner" [ELR].

The "Escalation Ladder Case Based Reasoner" [ELCBR] follows everything described above. Except:
1. Selection of the next rung in the non-amygdala-dominant branch is done via ELCBR case selection
   1. Which may incorporate the "stress" from the Amygdala, in order to slowly degrade the reasoner's ability to make optimal selection choices
1. After the rung selection is made, no matter how it was selected [Amygdala or ELCBR], a new case is inserted into the CBR, memoising what happened. 