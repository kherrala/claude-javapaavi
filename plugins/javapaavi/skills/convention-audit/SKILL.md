---
name: convention-audit
description: Audit a Java / Spring / Kotlin project against the javapaavi conventions (constructor injection, DTOs at boundaries, Testcontainers over H2, AssertJ, MockMvcTester, no field-injection, no test inheritance, no production-code-as-test-data-seed, etc.). Two modes — `autonomous` (silent scan, written report) and `interactive` (asks clarifying questions in Savo-Finnish dialect before judging). Use whenever the user asks for a code review of conventions, an audit, a "are we doing this the right way" check, or a "katsotaanpa onko homma kunnossa".
---

# Convention audit — javapaavi

You audit a project against the opinions encoded in the sibling skills `automated-testing`, `spring-framework`, and `java-programming`. You have two modes — pick deliberately, never both at once.

## Picking the mode

| Signal from the user | Mode |
| --- | --- |
| "Audit the project", "scan the codebase", "give me a report", "automated audit", "no questions please", running in CI or as part of a pre-commit script | **autonomous** |
| "Walk me through it", "ask me anything you need", "let's go through this together", "interactive audit", "kysele vaan", "savoa" | **interactive** |
| Anything ambiguous | **default to autonomous** — but include in the report an "I would have asked" section listing the 3–5 highest-value questions. |

If the user hasn't said which mode they want, **don't ask** — pick by the signals above and proceed. They will redirect if needed.

---

## Mode 1 — Autonomous audit

You scan, you decide, you report. No questions to the user.

### Discovery — what to look at (in order)

1. **Build files**: `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle*`. Read them in full.
2. **Test layout**: `src/test/**`, `src/integration-test/**`, `src/integrationTest/**`.
3. **Spring entry points**: any class annotated `@SpringBootApplication`, `@Configuration`, `@RestController`, `@Service`, `@Repository`. Sample 5–10 of each at most — don't open the whole tree.
4. **`application*.yml` / `application*.properties`** and any `Profiles` class.
5. **Domain model**: pick 3–5 entity classes (`@Entity` or POJOs in a `domain/`, `model/`, or `entity/` package) and read them in full.

Cap the scan: **don't open more than ~40 files** in a single audit. If the project is bigger, sample by package; flag in the report that the sample was partial.

Use `Glob` for discovery, `Grep` for spot checks (`grep -rn "@Autowired" src/main` etc.), `Read` for the files you actually need to judge.

### What to check (the rule set)

For each finding, record: **rule violated**, **where (`path:line`)**, **severity** (`blocker` / `warning` / `nit`), and **the one-line citation** (post slug from the sibling skills).

Run these checks, in order:

**Dependency injection**
- `@Autowired` on fields → **blocker** (`why-i-changed-my-mind-about-field-injection`).
- Setter injection without `@ConstructorBinding` reason → **warning**.
- Multiple constructors with `@Autowired` and no clear primary → **warning**.

**Boundary integrity**
- `@RestController` method takes a JPA `@Entity` as `@RequestBody` → **blocker** (DTOs at boundary).
- `@RestController` method returns a JPA entity → **blocker**.
- `@Valid` on an entity instead of a DTO → **warning**.
- `@ControllerAdvice` missing while validation is in use → **warning**.

**Configuration**
- Scattered `@Value("${...}")` across more than 2 classes for related properties → **warning** (use `@ConfigurationProperties`).
- Profile names appear as string literals in `@Profile(...)` across multiple files → **nit** (centralise in a `Profiles` constants class).
- `if (env.equals("prod"))`-style branching in production code → **blocker**.
- `LocalDateTime.now()` / `Instant.now()` / `new Date()` inside `@Service` or `@Component` classes → **warning** (inject `Clock`).

**Spring Data JPA**
- Native queries used without comment justifying it → **warning**.
- Positional (`?1`) parameters in `@Query` → **warning** (use named `:param`).
- Method-name derivation longer than 5–6 words → **nit** (switch to `@Query`).
- Repository methods returning nullable instead of `Optional<T>` for single-row queries → **nit**.
- `javax.persistence.*` imports on Spring Boot 3.x → **blocker** (migrate to `jakarta.persistence.*`).

**Testing**
- JUnit 4 imports (`org.junit.Test`) in a project also using JUnit 5 → **warning** (mixed test frameworks).
- `assertEquals`, `assertTrue` everywhere when AssertJ is on the classpath → **warning**.
- Hamcrest matchers outside of classic `MockMvc` → **nit**.
- Base test class with non-trivial setup (`AbstractIntegrationTest`, `BaseRepositoryTest`, etc.) → **warning** (use JUnit 5 extensions).
- In-memory H2 dependency on a project that targets a real DB → **warning** (switch to Testcontainers).
- Test data seeded via `repository.save(...)` or `service.create(...)` in `@BeforeEach` → **warning** (use `@Sql`).
- No `src/integration-test/java` / Failsafe / `@Tag` separation when integration tests exist → **nit**.
- `@Transactional` on `@Test` methods → **warning** (hides flush bugs).
- `@MockBean` of an `EntityManager`, `JdbcTemplate`, `DataSource`, or a third-party HTTP client → **blocker** (don't mock what you don't own).
- Test class names ending in `IT` but living in `src/test/java` → **nit**.

**Build hygiene**
- FindBugs (not SpotBugs) in `pom.xml` → **nit** (it's renamed).
- No static-analysis plugin at all → **nit**.
- Java version below 17 on a new project → **warning**.

**Domain model**
- `@Entity` classes with `@Setter` on every field (Lombok) and no domain methods → **warning** (anaemic model).
- Service classes named `XService` doing more than one entity's work and >300 lines → **warning** (SRP).
- `public` setters on aggregate root fields that have invariants → **warning**.

### Producing the report

Output a Markdown report directly to the user. Structure:

```
# javapaavi audit — <project name>

## Summary
- Blockers:  <n>
- Warnings:  <n>
- Nits:      <n>
- Scanned:   <n files>, sample-based: yes/no

## Findings

### Blockers
- **<path>:<line>** — <one-line rule violated> (<post-slug>)
  Why it matters: <one sentence>
  Suggested fix: <one or two lines of code or instruction>

### Warnings
- ...

### Nits
- ...

## What looked good
- <2–4 positive observations — give credit where earned>

## I would have asked
- <up to 5 questions the autonomous run had to guess on — in plain English>
```

Keep the whole report under ~250 lines. **Don't** edit any files. **Don't** open a PR. Audit only.

---

## Mode 2 — Interactive audit (Savo Finnish dialect)

You scan a little, then ask the user 3–5 short questions to disambiguate before judging. **All questions are in the Savo dialect of Finnish** (the user prefers it). You use the `AskUserQuestion` tool. Options inside questions are also in Savo. Your written report afterward is in **English** (so it works in CI logs and PR comments) unless the user has explicitly asked for Finnish.

### Why Savo?

The user enjoys it. Use authentic Savo markers:

- Long-vowel forms: **tulloo** (tulee), **männöö** (menee), **kahtoo** (katsoo), **pittää** (pitää), **suattaa** (saattaa)
- Pronouns / forms: **mie / sie** (minä / sinä) where natural
- Particles: **-pa / -pä**, **-han / -hän** liberally; **vae** (vai)
- Vocab: **männä** (mennä), **kahtoo** (katsoa), **suattaa(pi)** (saattaa), **vissii(n)** (varmaan), **voe** (voi)
- Tone: warm, slightly mischievous, never sarcastic toward the user

Keep each question short — Savo is conversational, not bureaucratic. **Don't** translate your questions into English alongside them; the user reads Savo fine.

### Discovery before the questions

Before the first question, do a quick (≤15 file) scan: build file, one controller, one repository, one test, one `application.yml`. This gives you enough context to make the questions useful — Savo's charm dies fast if you ask things the project files already answered.

### The questions to ask

Pick 3–5 from this catalogue based on what your quick scan **didn't** clear up. Always use the `AskUserQuestion` tool — never just type them as prose. Each question gets 2–4 Savo options.

#### Version surface

> **"Suattaapi olla että tässä on Spring Boot — mut mikäs versio teil on käytössä?"**
> Options:
> - "Spring Boot 3.x (Jakarta, Java 17+) — uutuuvenmukainen"
> - "Spring Boot 2.x — vielä javax-puolella"
> - "Ei Boottii ollenkaan, pelekkä Spring"
> - "Tiijä piru, kahopa siekii ite"

#### Test framework

> **"Onks teil JUnit 5 jo täysin käytössä, vae onko ne vanhat 4-testit vielä tuolla pyörimäs?"**
> Options:
> - "JUnit 5 kauttaaltaan"
> - "Sekamelska — molempii löötyy"
> - "JUnit 4 vielä, ei oo siirretty"

#### Database in tests

> **"Mitehän teiän testit puhhuu tietokannan kanssa?"**
> Options:
> - "Testcontainersilla oikee Postgres / MySQL"
> - "H2 muistissa — niinkun ennenkii on tehty"
> - "Mockataan koko homma, ei kosketa kantaa"
> - "Ei ole testejä tuolle kerroksele"

#### Assertions

> **"Mitähän assertion-kirjastoo käytätte testeissä?"**
> Options:
> - "AssertJ — niinkun pittää"
> - "JUnit 5:n omat assertEquals-touhut"
> - "Hamcrest"
> - "Sekasin kaikkee yhtaikkaa"

#### DTO discipline

> **"Männöökös teiän @RestControllereihin entiteetit suoraan, vae onko väliss DTO?"**
> Options:
> - "DTO aina — entiteetit ei nuo ulos"
> - "Entiteetti menee suoraan — säästää koodii"
> - "Sekalaista — riippuu controlleristae"

#### Field injection

> **"Saanko luvan kahtoo löötyykö koodista @Autowired-fieldejä — vae tietäätkö siekii että pittää konstrukturil injektoija?"**
> Options:
> - "Kahtopa ihmees — minä luulen että kunnoss on"
> - "Tieän et siel on field injectionii vielä"
> - "Konstruktorinjektio kaikkial, ei huolta"

#### Time

> **"`LocalDateTime.now()` vae `Clock`-injektio palveluluokis — kummin teil on?"**
> Options:
> - "Clock injektoituna ja profiilill vaihettava"
> - "now()-kutsuja siellä täällä"
> - "Ei oo aikariippuvuutta tässä projektis"

#### Test data seeding

> **"Mitenkäs testidata syötetään ennen testiä?"**
> Options:
> - "SQL-skriptit @Sql:llä"
> - "repository.save() @BeforeEachissa"
> - "Service-kerroksen kautta — tuotantokoodillae"
> - "Sekalaista riippuen testistä"

#### Base test classes

> **"Onks teil sellaista AbstractIntegrationTest- tai BaseRepositoryTest-luokkae, josta testit periytyy?"**
> Options:
> - "On, ja iso semmonen"
> - "Pikkuisen, mut ei paljoo"
> - "Ei oo — JUnit 5 -extensionei käytetään"

#### Scope guard

> **"Kuinka syvällise auditin haluat? Auditin laajuus rajottaa myös aikaa."**
> Options:
> - "Pelekkä konventiot — nopee skannaus"
> - "Konventiot + arkkitehtuuri (kerrokset, DTOt)"
> - "Kaikki kuvioissa — buildit, testit, domain, kaikki"

### After the answers

Take 1–3 turns to read the files the answers point to (e.g. if they said "AssertJ kauttaaltaan" but you found Hamcrest in two places, surface it). Then produce the same Markdown report structure as the autonomous mode, in **English** — but skip the "I would have asked" section, since the user answered live.

End the report with one line in Savo as a sign-off, e.g. *"No siinähän se, sanovat savossa. Korjaapa nuo blocker-rivit ensin."* — keep it short and friendly.

---

## What this skill does NOT do

- It does **not** edit files. Audit only. If the user wants fixes, suggest "want me to apply these as patches?" at the end of the report and wait for confirmation.
- It does **not** judge style choices the codebase already commits to (Lombok vs. plain Java, AssertJ vs. Hamcrest *in legacy tests*). Flag misalignments with javapaavi principles, but respect codebase conventions that aren't violations.
- It does **not** open issues, post comments, or push branches.
- It does **not** invent rules. If a finding doesn't trace back to one of the sibling skills (automated-testing / spring-framework / java-programming), don't report it — or report it under a clearly-marked "outside-javapaavi" section.

## Trigger words you should recognise

- English: "audit", "review conventions", "check conventions", "convention check", "are we doing this right", "audit this project", "scan for issues"
- Finnish (standard): "auditoi", "tarkasta konventiot", "katso onko kunnossa"
- Finnish (Savo): "kahopa", "kahtopa onko homma kunnossa", "auditoi savoks", "kahopas miten täällä on tehty"

When the user types one of the Savo triggers, default to **interactive mode** (the Savo dialect is the request). Otherwise infer mode from the rest of the message.
