# Process Notes

## Starting idea

The project began as a small, self-contained desktop pet for a cozy study desk. The intended user is a student taking a short break between study tasks. The initial interaction was to drag and throw the pet, while a simple physics model kept it on-screen and let it bounce on the desk.

## Design and implementation changes

The initial prototype used a procedural witch-hat character. It was later redesigned as a pink-haired, cat-eared chibi character inspired by the visual reference supplied during development. The new sprite is drawn with Pygame shapes rather than a copied image, so the project does not depend on external art files. The autonomous state machine was also extended with walking, resting, napping, grooming and looking-around poses.

The click-to-cheer response sits alongside drag-and-throw: a click makes the character bounce, show floating hearts, become happy, and display a short message. A brief cooldown makes rapid repeat clicks harmless and explains why another cheer did not trigger. The room was then extended with a procedural chair and bed; the autonomous state machine can route the pet to sit or nap there and return to its floor position. Furniture destinations follow the resizable scene layout, and a bed visit restores energy. These additions make the room feel more lived-in while keeping the experience self-contained and testable without external services or art assets.

## User trial and iteration

**Not completed yet.** The assignment asks for at least one other person to try the experience before receiving an explanation. No trial has been conducted or observed in this development session, so there are no user observations to report and no changes are being attributed to a trial. Before submission, ask someone to try the app without instructions, note where they hesitate or what they misunderstand, make or justify one adjustment, and replace this section with the real observation and decision. Do not include identifying details.

## AI tools and decisions

An AI coding assistant was used to help plan and implement the prototype, autonomous behaviors, procedural character drawing, README updates, the click-to-cheer interaction, and furniture visits. One suggestion kept was to make the user action produce an explicit response and visible feedback; this led to the happy bounce, floating hearts, message, and energy change. Furniture was added as a small extension of the autonomous state machine rather than as a new user control. The implementation is checked with the project's uv-managed headless smoke test and Python compilation check.

## Credits

- The motion model follows the Week 7 lecture's `Ball` example, using position (`x`, `y`), velocity (`vx`, `vy`) and gravity. The project extends that foundation with a pet state machine, cursor dragging, throw velocity, boundary handling, and soft floor bounce.
- The procedural animation approach is informed by the Week 5 frame-sequence concept; the pet's poses and expressions are drawn in code rather than copied from course assets.
- The current cat-eared character is an original procedural interpretation of the visual reference provided by the project author. No external image assets, sounds, data, or AI service are included in the application.
