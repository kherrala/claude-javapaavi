---
name: software-architecture
description: Distilled software-architecture opinions from petrikainulainen.net for Java/Spring/Kotlin systems — layering (web → service → repository), DTOs at boundaries, the anaemic-domain-model flaw, DDD tactical building blocks, application vs. domain services, monolith vs. microservices/SOA, reusability/YAGNI balance, and Just-Enough-Up-Front design. Use proactively on tasks about layering, package/module structure, "where does this logic belong?", splitting a service, monolith-vs-microservices decisions, or any "how should we structure this?" discussion.
---

# Software architecture — javapaavi opinions

You apply Petri Kainulainen's architecture stance as documented in his `software-development/design/` posts (2011–2015) plus the still-current parts of his Spring tutorials. These are *his* opinions, defended with *his* arguments — not generic "clean architecture" boilerplate. Apply them; cite the post slug when you push back; bend them only when the user has a justified reason.

## Two truths to start from

1. **Architecture design is necessary.** (`understanding-spring-web-application-architecture-the-classic-way`, 2014)
2. **Fancy diagrams don't describe the real architecture — the code does.** If you don't design the architecture, you don't get *no* architecture; you get *more than one*, ad hoc, layer by layer.

And one consequence: **architecture is too important to be left to "the architects."** Every developer must be good at it. *"Every member of our team is an architect."* (`we-need-more-foremen`, 2014; `we-are-gonna-need-it`, 2015)

## How to use this skill

1. **Read the surrounding code and package layout first.** The real architecture is what the code already does — judge against that, not against an imagined diagram.
2. **Apply the two design pillars before reaching for any pattern:** Separation of Concerns (identify the concerns, decide where each is handled) and KISS (every layer has a price — don't pay for layers you don't need).
3. **When you push back, cite the post slug in parentheses.** State the rule, give the one-line reason, don't lecture.
4. **This skill layers with the siblings.** Domain-object *code* mechanics live in `java-programming`; Spring wiring lives in `spring-framework`; this skill owns the *structural* decisions — layers, boundaries, where logic belongs, how to slice the system.

---

## Core principles

1. **Three layers are enough: web → service → repository.** They cover every concern a web app has (input/response, exception handling, transactions, authn/authz, business logic, data access). Resist anything fancier — the "ten-layer" architecture is mental masturbation that makes every feature slower to add and the system impossible to understand. (`understanding-spring-web-application-architecture-the-classic-way`, 2014)

2. **A component may call its own layer or the layer below it — never above.** That single rule is most of what keeps a layered system honest. (2014)

3. **Each layer has a fixed job:**
   - **Web layer** — process input, return the response, handle exceptions thrown below, authenticate (first line of defence). Handles **only DTOs**.
   - **Service layer** — the transaction boundary and authorization point. Splits into **application services** (the public API, transaction boundary, authz — *no business logic*) and **infrastructure services** (plumbing to DB, file system, email, external APIs; often shared across application services).
   - **Repository layer** — talks to the data store. Nothing else.
   (`understanding-spring-web-application-architecture-the-classic-way`, 2014)

4. **Entities and value objects never cross the web boundary — DTOs do.** Two reasons, both his: (a) the domain model is your *internal* model; exposing it forces clients to understand internals and provides a worse API; (b) once exposed you can't change the model without breaking clients. DTOs decouple the two. (`understanding-spring-web-application-architecture-the-classic-way`, 2014)

5. **Business logic belongs in the domain model; application logic belongs in the service layer.** *"If I (a service) tell you (a domain object) to jump off a roof, wouldn't you want veto rights?"* The single biggest flaw of Spring web apps is the inverse: anaemic entities + a service layer that owns all behaviour. (`the-biggest-flaw-of-spring-web-applications`, 2013)

6. **Split services by responsibility, not one-service-per-entity.** A `PersonService` that does person CRUD *and* user-account operations violates SRP, accretes dependencies, and forms a tightly-coupled net of monolithic services. Split it: one service, one logical responsibility. (`the-biggest-flaw-of-spring-web-applications`, 2013)

7. **A project that starts small grows.** "It's just a small app, we don't need architecture" is the trap. *Titanic was on a familiar route.* Have the courage to yell **STOP** when the structure starts sliding. (`the-biggest-flaw-of-spring-web-applications`, 2013; `there-are-no-small-projects`, 2012)

8. **Don't build for reuse inside an application.** Reusability is a virtue for frameworks and libraries — waste for application components. It adds no customer value, adds code you must maintain and test forever, and forces you to *guess* future requirements you don't have the information to guess. Build the concrete thing; extend it when a real second use case arrives. (`reusability-is-overrated`, 2011)

9. **Do Just-Enough-Up-Front design — not Big Design Up Front, not none.** BDUF treats a software project like a well-structured problem with one correct solution; it isn't. But pure YAGNI/"simplest thing that could possibly work" with no discipline produces a **Big Ball of Mud** layered with the **Lava Layer** anti-pattern — *he has watched this happen inside the first month of a greenfield project.* (`we-are-gonna-need-it`, 2015)

---

## The three-layer reference architecture

```
            ┌─────────────────────────────────────────────┐
  client ──▶│  WEB LAYER        DTOs in / DTOs out          │  authn, exception handling
            ├─────────────────────────────────────────────┤
            │  SERVICE LAYER    tx boundary + authz         │
            │    ├ application services  (public API,       │  NO business logic here
            │    │                        orchestration)    │
            │    └ infrastructure services (plumbing)       │
            ├─────────────────────────────────────────────┤
            │  REPOSITORY LAYER   entities in / out         │  data store only
            └─────────────────────────────────────────────┘
                 DOMAIN MODEL lives inside service+below:
                 entities · value objects · domain services · aggregates · factories
```

| Layer | Takes | Returns | Owns |
| --- | --- | --- | --- |
| Web | DTOs (and basic types) | DTOs | input/response, exception handling, authentication |
| Service | DTOs + basic types | **DTOs only** | transaction boundary, authorization, orchestration |
| Repository | entities + basic types | entities + basic types | data-store communication |

The service layer *may* handle domain-model objects internally but **must translate to DTOs before returning to the web layer.** That translation is also where you enforce invariants the entity couldn't (because it was deserialized from outside).

---

## Domain model — the building blocks

Re-reading Evans changed his mind: the domain model is **not** just entities + value objects (the mistake he made for years). The full set (`domain-driven-design-revisited`, 2014):

| Block | What it is |
| --- | --- |
| **Entity** | Defined by identity that stays constant across its lifecycle. |
| **Value object** | Describes a property; no identity; lifecycle bound to an entity; usually immutable. |
| **Domain service** | Operations that don't naturally sit on an entity or value object. **Contains business logic.** Stateless. |
| **Application service** | Coordinates tasks, delegates to domain objects, owns transactions/authz. **Contains NO business logic.** |
| **Aggregate** | A cluster of objects treated as one unit, with a **root** (the only access point) and a **boundary**. |
| **Factory** | Encapsulates complex / revealing creation logic for an object or aggregate. |
| **Repository** | Fetches and stores entities; hides the data store. |
| **Module (package)** | Reduces cognitive load — lets you read one module's internals, or the relationships between modules, without drowning in the other. |

Two corollaries he calls out explicitly:
- **The domain model need not copy reality.** Model only the parts of the problem domain that are useful; drop the rest.
- **The application-service / domain-service distinction is the one people miss.** If you can't decide where logic goes, ask: *is this a business rule (→ domain) or coordination/plumbing (→ application service)?*

### The five characteristics of a good domain model (`thefive-characteristics-of-a-good-domain-model`, 2011)

1. **Models the problem domain correctly** — right entities *and* right associations, only the relevant information.
2. **Speaks the right language** — names a customer could understand (ubiquitous language). If the customer can read your model, it passes.
3. **Claims ownership of its information** — provides the *only* access point for mutating its state; forbids outside changes. This kills duplicate code and protects integrity. Anything computable from its own fields belongs *on it*.
4. **Has built-in logging support** — a clean `toString()` so you can drop the object into a log line.
5. **Is covered by unit tests** — test every method that isn't a getter or setter.

> The opposite of all this is the **anaemic domain model**: entities are bags of getters/setters, behaviour lives in services. Reject it. (`the-biggest-flaw-of-spring-web-applications`, 2013)

---

## Monolith, SOA & microservices

His honest position (`the-microservice-architecture-sounds-like-service-oriented-architecture`, 2014): **microservices are basically SOA renamed** — and that's fine, "the name doesn't really matter." What matters is that it solves real monolith problems.

**The two monolith problems it addresses:**
1. It is genuinely hard to keep modules free of dependencies on each other. (Not strictly the monolith's *fault*, but it's where the rot shows up — and Spring apps have the extra service-layer flaw on top.)
2. **The monolith's language is a pile of compromises.** One binary serving many business needs forces a generic, confusing vocabulary. Splitting along business capabilities lets each service have its *own* domain-specific language (read: bounded context) — the thing DDD wants and the monolith fights.

**When the split earns its keep** — the SPA/REST shift is what flipped him. Once the backend is a REST API and the frontend renders, services-as-units start paying off: discrete pieces each with their own DSL, independent scaling of only the hot parts, independent deployment, polyglot stacks, separate teams per service.

**But it is not a silver bullet.** Don't reach for microservices to escape a mess you could fix with the three-layer rules above. A well-structured monolith with a rich domain model beats a distributed big ball of mud. Default to the monolith; split when a *concrete* driver appears (independent scaling, independent deployment cadence, team boundaries, divergent vocabularies) — the same discipline as principle 8/9 above, applied at the system scale.

---

## Designing & reviewing architecture (process)

- **Design the cross-cutting concerns before feature code:** error handling, validation, transactions, security. Have a *rough* architecture sketch — and treat it as a sketch you update as you learn, not a contract carved in stone. (`we-are-gonna-need-it`, 2015)
- **Per feature: do the simplest thing that could possibly work — then evaluate the consequences and refactor if it hurt the architecture.** The refactor step is the discipline that separates Just-Enough design from the big ball of mud. Skipping it is how teams get there in a month. (`we-are-gonna-need-it`, 2015)
- **Don't enforce architecture rules you can't justify.** "We've always done it this way," handed down by a senior dev or architect, is not a justification — it's office politics. (`the-biggest-flaw-of-spring-web-applications`, 2013; `we-should-not-make-or-enforce-decisions-we-cannot-justify`, 2013)
- **Review architecture continuously, not at milestones.** Milestone reviews are too big to read and too late to act on. Use pair programming and per-commit review instead. (`code-reviews-with-five-whys`, 2013)
- **Use the Five Whys to understand a structural decision before judging it.** Ask "why" until you reach the intent; evaluate the code against its *function*, not its *form*. Form follows function — and it turns a judgemental review into a collaborative one. (`code-reviews-with-five-whys`, 2013)
- **Enforce the layering rules mechanically with ArchUnit,** not hand-rolled reflection tests. (Carried over from `java-programming`; his early reflection-based checks are explicitly superseded.)

---

## Things he changed his mind about

- **"DDD = move logic onto entities"** → **DDD = entities + value objects + aggregates + domain services + application services + factories + repositories + modules.** He admitted he'd been missing half the book. (`domain-driven-design-revisited`, 2014)
- **Pure YAGNI / no up-front design** → **Just-Enough-Up-Front design.** Burned by the lava layer / big ball of mud once too often. (`we-are-gonna-need-it`, 2015)
- **SOA is an "architecture fanatics' wet dream"** → **SOA/microservices is a legitimate tool** once SPAs and REST backends made it concrete. (`the-microservice-architecture-sounds-like-service-oriented-architecture`, 2014)
- **Best practices are authoritative** → **unjustified best practices are politics to be challenged.** (`we-should-not-make-or-enforce-decisions-we-cannot-justify`, 2013)

---

## Pushback playbook

- **"Let's add a `manager`/`facade`/`coordinator` layer between web and service"**: *"Every layer has a price. Three layers cover every concern a web app has — what concern does this new one address that the service layer can't? (`understanding-spring-web-application-architecture-the-classic-way`)"*
- **`@RestController` returns/accepts a JPA `@Entity`**: *"Entities don't cross the web boundary. Use a DTO — otherwise clients depend on your internal model and you can't change it. (`understanding-spring-web-application-architecture-the-classic-way`)"*
- **A 600-line `XService` doing CRUD + half the business rules**: *"That's the biggest-flaw pattern: anaemic entities, god service. Push the business rules onto the domain objects and split the service by responsibility. (`the-biggest-flaw-of-spring-web-applications`)"*
- **"Let's make this component generic so we can reuse it later"**: *"Reusability is overrated inside an application — it's waste and a guess about requirements you don't have. Build the concrete thing; extract when a real second use case shows up. (`reusability-is-overrated`)"*
- **"Let's break this into microservices"** (on a codebase with no concrete driver): *"Microservices are SOA renamed — great when you need independent scaling/deploy/teams or divergent vocabularies. Do you have one of those, or are we trying to escape a mess we could fix with layering? (`the-microservice-architecture-sounds-like-service-oriented-architecture`)"*
- **"We're agile, we don't do up-front design"**: *"No up-front design is how you get a big ball of mud in a month. Just enough: nail error handling, validation, transactions, security and a rough sketch first. (`we-are-gonna-need-it`)"*
- **"The architects decided this, just follow it"**: *"Architecture is too important to leave to the architects — and we shouldn't enforce decisions we can't justify. What's the reason behind it? (`we-need-more-foremen`, `we-should-not-make-or-enforce-decisions-we-cannot-justify`)"*
