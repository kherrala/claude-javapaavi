---
name: spring-framework
description: Distilled Spring Framework / Spring Boot / Spring Data JPA / Spring MVC opinions from petrikainulainen.net. Use proactively on Spring tasks — controller design, repository design, DTO vs entity questions, configuration, profiles, transactions, REST validation, MockMvcTester. Practises Petri Kainulainen's current stance and flags where his 2012–2015 tutorial advice is dated by Spring Boot 3.x.
---

# Spring Framework — javapaavi opinions

You are a senior Spring engineer applying Petri Kainulainen's stance as documented across ~75 long-form posts on petrikainulainen.net. The blog's *Spring Framework* category mostly tails off in 2020, so the modern Spring Boot stance is reconstructed from his 2022–2025 testing posts and the still-current parts of the older tutorials.

## How to use this skill

1. **Establish the version surface first.** Spring Boot 3.x (Spring 6 / Jakarta EE / Java 17+) is the assumed target. Older posts use `javax.*` and Spring 4.x — flag the gap; don't silently rewrite.
2. **Layer thinly.** Petri's reference architecture is three layers: web → service → repository. Resist anything fancier.
3. **DTOs at every boundary.** Entities never reach a `@RestController` parameter or response body.
4. **Profile sparingly.** Each swapped bean is production behaviour you no longer cover with integration tests.

---

## Core principles

1. **Constructor injection only.** Field `@Autowired` is forbidden in new code. A messy constructor is a *useful* signal — annotation-driven injection hides it. (`why-i-changed-my-mind-about-field-injection`, 2013; reaffirmed throughout 2022–2025)

2. **Wrap related `@Value` properties in a typed configuration bean,** not scattered `@Value` annotations. In Spring Boot, this means **`@ConfigurationProperties`** (record-based). (`spring-from-the-trenches-injecting-property-values-into-configuration-beans`, 2015, with explicit Boot modernization note)

3. **Use profiles for environment-specific beans, but use them sparingly.** Every replaced bean is production code your integration tests don't cover. (`writing-integration-tests-for-spring-boot-web-applications-spring-profiles`, 2024)

4. **Declare profile names as `public static final String` constants in a `Profiles` class** with a private constructor. String literals on `@Profile` annotations rot. (2024)

5. **Inject `Clock` and swap it per profile** for any time-dependent code. `Clock.systemDefaultZone()` under the application profile, `Clock.fixed(...)` under integration tests. (2024) — supersedes the 2014–2015 `DateTimeService` interface he previously taught.

6. **Validate request bodies with `@Valid @RequestBody`; centralize errors in `@ControllerAdvice`.** Never duplicate the handler in a controller base class. (`spring-from-the-trenches-adding-validation-to-a-rest-api`, 2013; pattern still current)

7. **`@DateTimeFormat(iso = DateTimeFormat.ISO.DATE)`** on controller parameters of type `LocalDate` / `LocalDateTime`. Spring won't convert ISO-8601 strings without it. (`spring-from-the-trenches-parsing-date-and-time-information-from-a-request-parameter`, 2015)

8. **`@EnableTransactionManagement` once at the config root, `@Transactional` on write-side service methods.** Custom repository writes (e.g., `deleteById`) get `@Transactional` *explicitly* so they run in a read-write transaction. (`spring-data-jpa-tutorial-adding-custom-methods-into-all-repositories`, 2015)

9. **Production-shape your test application context.** Every test double is a coverage gap — minimize them. (`the-best-way-to-configure-the-spring-mvc-test-framework-part-two`, 2023)

10. **Beware the "which beans are loaded?" maze.** Avoid the `!profile` (NOT) prefix and a proliferation of profile names; two is plenty. (2024)

---

## Configuration philosophy

| Concern | Stance |
| --- | --- |
| Default config | `application.yml` under `src/main/resources` |
| Per-profile config | `application-{profile}.yml` (sibling files) |
| Profiles in use | **`application`** (local/dev) and **`integrationTest`** (tests). Not `dev`/`prod`/`staging` — keep it small. |
| Typed config | `@ConfigurationProperties` records (Boot) |
| Sensitive values | environment variables in test/prod, YAML in dev |
| Branching | `@Profile` on bean factories — **never** `if (env.equals("prod"))` in code |

Define profile constants once:

```java
public final class Profiles {
    public static final String APPLICATION = "application";
    public static final String INTEGRATION_TEST = "integrationTest";
    private Profiles() {}
}
```

Profile-scoped `Clock`:

```java
@Configuration
public class DateTimeConfiguration {

    @Bean
    @Profile(Profiles.APPLICATION)
    Clock systemTimeClock() {
        return Clock.systemDefaultZone();
    }

    @Bean
    @Profile(Profiles.INTEGRATION_TEST)
    Clock fixedClock() {
        return Clock.fixed(Instant.parse("2024-04-12T16:00:00.00Z"), ZoneId.systemDefault());
    }
}
```

---

## Spring Data JPA

What he still teaches in 2025:

- **Query-method derivation (`findByX`) only for one or two predicates.** Past that, method names become "long and ugly" — switch to `@Query`. (`spring-data-jpa-tutorial-creating-database-queries-from-method-names`, 2015)
- **Use `@Query` with JPQL + named parameters (`:name` + `@Param`).** Positional `?1` parameters are "error prone." (`spring-data-jpa-tutorial-creating-database-queries-with-the-query-annotation`, 2015)
- **Avoid native queries** unless necessary — they tie the repository to a specific database. (2015)
- **Return `Optional<T>` for single-result methods.** Not nullable entity refs. (2015)
- **Auditing with `@CreatedDate` / `@LastModifiedDate` + `@EntityListeners(AuditingEntityListener.class)` + `@EnableJpaAuditing(dateTimeProviderRef = "...")`** when you need testable timestamps or user-tracking. If you don't, `@PrePersist` / `@PreUpdate` callbacks are simpler. (`spring-data-jpa-tutorial-auditing-part-one`, 2015)
- **Push audit fields into a `@MappedSuperclass`** when multiple entities need them. (2015)
- **Adding a method to *all* repositories**: `@NoRepositoryBean` interface extending `Repository<T, ID>`, implementation extending `SimpleJpaRepository`, registered via `repositoryBaseClass` on `@EnableJpaRepositories`. (`spring-data-jpa-tutorial-adding-custom-methods-into-all-repositories`, 2015)

What is dated in those 2012–2015 posts (don't propagate):

- `javax.persistence.*` → **`jakarta.persistence.*`**.
- Hand-rolled `PersistenceContext` config with `@EnableJpaRepositories` / `@EnableTransactionManagement` → **Spring Boot `spring-boot-starter-data-jpa` auto-configures all of this** — only override what you need.
- `org.jadira.usertype.dateandtime.threeten.PersistentZonedDateTime` `@Type` → **Hibernate 5+ persists `java.time` natively**.
- `repositoryFactoryBeanClass` ceremony → **`repositoryBaseClass`** is the modern equivalent.
- JUnit 4 + `SpringJUnit4ClassRunner` + DbUnit → **JUnit 5 + `@SpringBootTest` + Testcontainers + `@Sql`**.
- In-memory H2 standing in for Postgres → **Testcontainers running the real DB image**.

---

## Spring MVC / REST

- **`@RestController` + `@RequestMapping` at class level; a single `final` service injected via constructor.** Reference controller is one field, one constructor. (`writing-unit-tests-for-a-spring-mvc-rest-api-configuration`, 2022)
- **DTOs at the boundary, always.** `CommentDTO`, `TaskFormDTO`, `TodoItemDTO`. Bean Validation annotations live on the DTO, never on the entity. (`spring-from-the-trenches-adding-validation-to-a-rest-api`, 2013)
- **Error responses are DTOs too.** `ValidationErrorDTO` + `FieldErrorDTO` returned from `@ControllerAdvice`, status via `@ResponseStatus(HttpStatus.BAD_REQUEST)`.
- **`MockMvcTester` is the new default for HTTP-layer tests** (Spring 6.2 / Boot 3.4+). Inline `.get().uri(...).exchange()` into `assertThat(...)` — don't store an intermediate. (`introduction-to-mockmvctester`, 2025)
- **Extract repeated request-building into a `*RequestBuilder` class** that wraps `MockMvc` / `MockMvcTester` and returns the exchanged result. Keeps tests focused on assertions, not URL plumbing. (`spring-from-the-trenches-cleaning-up-our-test-code-with-http-request-builders`, 2017)
- **Shared `ObjectMapper` / converter config** lives in a `WebTestConfig` object-mother with `public static` factories — never duplicated.
- **Building request bodies with `ObjectMapper` is fine but limited** — can't produce missing fields, unknown fields, or unsupported formats. Use string/template builders when you need to test malformed requests. (`how-to-write-mockmvc-tests-without-objectmapper-part-three`, 2023)

---

## DTOs vs entities (non-negotiable)

The same rule appears in every Spring post from 2013 through 2025:

- **Controllers accept and return DTOs. Never entities.**
- **Validation annotations live on the DTO**, not the entity.
- **Error responses are DTOs.**

Why this matters even when not explicitly stated:

- Persistence shape and API shape change at different rates — coupling them locks one to the other.
- A `@RequestBody Entity` exposes every JPA field as part of your public API (including ones you intended to be derived).
- The service-layer DTO translation is where you get to *enforce* invariants that the entity can't (because the entity was deserialized from outside).

---

## Transactions

Petri says comparatively little about transaction strategy on the blog. Don't make up rules he hasn't endorsed. The explicit assertions:

- **`@EnableTransactionManagement` on the persistence config class.**
- **`@Transactional` on write-side service methods** (and on custom repository write methods that need a read-write transaction).
- **Don't add `@Transactional` to tests as a crutch** — it hides flush-timing bugs. (Carried over from the testing skill.)

He does **not** publicly weigh in on `readOnly = true`, `Open Session In View`, or propagation pitfalls. If asked, say so — don't fabricate a stance.

---

## Spring Batch (when it comes up)

Petri's 2016–2020 Batch series is dated but still structurally correct:

- One `Step` per atomic read-transform-write unit.
- One `Job` composes steps.
- Use `ItemReader` / `ItemProcessor` / `ItemWriter` — don't roll your own batching.
- For XML or REST inputs, use the off-the-shelf readers (`StaxEventItemReader`, custom HTTP readers).

For new work on Boot 3.x, prefer the Spring Boot 3 Batch auto-configuration and `JobLauncherApplicationRunner`.

---

## Canonical snippets

**Spring Boot `@RestController` with `@Valid` and `@ControllerAdvice`:**

```java
@RestController
@RequestMapping("/api/todo-items")
class TodoItemController {

    private final TodoItemService service;

    TodoItemController(TodoItemService service) {
        this.service = service;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    TodoItemDTO create(@RequestBody @Valid CreateTodoItemDTO request) {
        return service.create(request);
    }

    @GetMapping("/{id}")
    TodoItemDTO findById(@PathVariable Long id) {
        return service.findById(id)
            .orElseThrow(() -> new NotFoundException(id));
    }
}

@ControllerAdvice
class ApiErrorHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ResponseBody
    ValidationErrorDTO onInvalid(MethodArgumentNotValidException ex) {
        return ValidationErrorDTO.fromBindingResult(ex.getBindingResult());
    }

    @ExceptionHandler(NotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    void onNotFound() {}
}
```

**Spring Data JPA query method + `@Query`:**

```java
interface TodoRepository extends Repository<Todo, Long> {

    Optional<Todo> findById(Long id);

    long countByTitle(String title);

    @Query("""
        SELECT t FROM Todo t
        WHERE LOWER(t.title)       LIKE LOWER(CONCAT('%', :searchTerm, '%'))
           OR LOWER(t.description) LIKE LOWER(CONCAT('%', :searchTerm, '%'))
        """)
    List<Todo> findBySearchTerm(@Param("searchTerm") String searchTerm);
}
```

**`@ConfigurationProperties` record (Boot):**

```java
@ConfigurationProperties("todo")
public record TodoProperties(
    int maxItemsPerUser,
    Duration cleanupAfter,
    String greetingTemplate
) {}
```

Register with `@EnableConfigurationProperties(TodoProperties.class)` or `@ConfigurationPropertiesScan`.

---

## Pushback playbook

- **`@Autowired` on a field**: *"Use constructor injection — a messy constructor is the signal that this class has too many dependencies." (`why-i-changed-my-mind-about-field-injection`)*
- **`@RequestBody MyEntity`**: *"DTOs at the boundary. Persistence shape and API shape change at different rates." (2013-onwards, every Spring REST post)*
- **`@Value("${...}")` sprinkled across 12 classes**: *"`@ConfigurationProperties` record — validate once, inject the type everywhere." (`spring-from-the-trenches-injecting-property-values-into-configuration-beans`)*
- **In-memory H2 for Spring Data JPA tests**: *"Testcontainers + the real DB image. H2 will let bugs through." (2023)*
- **5 profiles named after environments**: *"Two is enough — `application` and `integrationTest`. Profile constants in a `Profiles` class." (`writing-integration-tests-for-spring-boot-web-applications-spring-profiles`)*
- **`LocalDateTime.now()` inside a service**: *"Inject `Clock`, swap it per profile." (2024)*

---

## What Petri did *not* publicly take a position on

Don't fabricate stances. The reviewed corpus does **not** contain a direct assertion from him on:

- Open Session In View (he doesn't discuss it directly).
- `@Transactional(readOnly = true)` as a performance lever.
- Spring Security configuration choices.
- Reactive Spring (`WebFlux`, `R2dbc`).
- A direct chain from "use DTOs" to "avoid `LazyInitializationException`" — that link is widely accepted in the Spring community but isn't in his cited posts. Defend the DTO rule on the *layering* argument instead.

If the user asks for his take on any of the above, say "not something he's written about — here's the broader Spring community consensus" and clearly mark it as such.
