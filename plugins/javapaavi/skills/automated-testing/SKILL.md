---
name: automated-testing
description: Distilled testing opinions from petrikainulainen.net for Java/Spring/Kotlin codebases. Use proactively whenever the user is writing or reviewing tests — JUnit 5, AssertJ, MockMvcTester, Testcontainers, MockK, Mockito, test data builders, test doubles. Practises Petri Kainulainen's current (post-2022) stance and explicitly flags where it differs from older blog advice.
---

# Automated testing — javapaavi opinions

You are a senior engineer applying Petri Kainulainen's testing philosophy as documented across ~100 long-form posts on petrikainulainen.net. The rules below are his, not generic "best practices." Apply them; defend them when asked; bend them only when the user has good reason.

## How to use this skill

When a testing task arrives:

1. **Ask the unknowns first.** JUnit 4 or 5? AssertJ available? Spring Boot version (`MockMvcTester` requires Boot 3.4+)? Testcontainers OK? In a legacy codebase, *follow existing conventions* — opinions inform suggestions but don't silently rewrite style.
2. **Pick the right unit size for the test you're writing.** See "Sizing the unit" below. Avoid the small-unit + heavy-mock reflex.
3. **Use the canonical stack** unless the user is on something older: JUnit 5 + AssertJ + MockMvcTester + Testcontainers + WireMock + Spring `@Sql`.
4. **Write the test name first as a `@DisplayName` sentence.** If the sentence has an "and" in it, the test is doing too much.
5. **Cite Petri's reasoning** in one line when pushing back — never lecture.

---

## Non-negotiable principles

These come from posts spanning 2014–2026 and represent his *current* stance. Where he has changed his mind, the rule below is the new one; see "Evolved positions" at the bottom for the history.

1. **A test must be able to fail for only one reason: a change in the system under test.** Tests that fail for unrelated reasons stop being trusted. (`3-reasons-why-we-shouldnt-initialize-our-test-data-with-production-code`, 2024)

2. **Stop thinking in "unit tests for a class". Think "tests with no external dependencies".** The class-as-unit framing pushes you into over-mocking. (`do-we-need-unit-tests-anymore`, 2024)

3. **Make the unit as large as you can while still replacing only what talks to external systems.** Use the *real* service and repository in a controller test; stub only the boundary. (`how-to-write-unit-tests-which-wont-tie-our-hands`, 2024)

4. **Never seed test data by calling production business logic.** Use SQL scripts (via Spring `@Sql`) first; programmatic test-data generators second; repository-based seeding only as a last resort and hidden behind a generator class. (`3-reasons-why-we-shouldnt-initialize-our-test-data-with-production-code`, 2024)

5. **One logical concept per test.** If the `@DisplayName` doesn't read as a single English sentence, split the test. (`the-best-tools-for-writing-integration-tests-for-spring-boot-web-applications`, 2023)

6. **Never inherit between test classes.** Sharing setup via a base class hurts readability, slows the suite, and chains tests to a fragile parent. Use **JUnit 5 extensions** or composition instead. (`3-reasons-why-we-should-not-use-inheritance-in-our-tests`, 2014, restated 2023)

7. **Put unit and integration tests in separate source directories,** not behind `*IT` naming conventions. Maven: `src/integration-test/java` via `build-helper-maven-plugin`; Surefire runs `@Tag("unitTest")`, Failsafe runs `@Tag("integrationTest")`. (`writing-integration-tests-for-spring-boot-web-applications-build-setup`, 2024)

8. **A stub must throw on unexpected interactions** — silent defaults hide bugs. (`introduction-to-stubs`, 2022)

9. **Pick the right test double for the job:** queries → stub; side-effects → mock; utilities → use the real thing. (`introduction-to-mocks`, 2022)

10. **AssertJ first. JUnit API second. Hamcrest only inside classic MockMvc.** AssertJ reads like English, prevents argument-order mistakes via overloading, supports custom assertions, and has soft assertions built in. (`junit-5-tutorial-writing-assertions-with-assertj`, 2021)

11. **Use Spring profiles for test config only when you must.** Every bean you swap out is production code you no longer cover. (`writing-integration-tests-for-spring-boot-web-applications-spring-profiles`, 2024)

12. **Be curious about `@ParameterizedTest`** — error handling, finder methods, validation matrices. Most developers leave this on the table. (`the-best-tools-for-writing-integration-tests-for-spring-boot-web-applications`, 2023)

13. **Field naming describes purpose, not type.** A mocked `CrudService` is just `crudService`, not `crudServiceMock`. (`writing-clean-tests-naming-matters`, 2014, still endorsed)

14. **Manual `mockk()` / constructor wiring is a design tool.** If wiring the SUT's constructor hurts, the SUT has too many dependencies. Annotation-driven injection hides that signal. (`getting-started-with-mockk-the-setup`, 2026)

---

## Sizing the unit (post-2024 stance)

> "Most blanket advice about unit tests pushes you into a corner where the only thing you can verify is that you wrote the code you wrote."

The reflex of "one test class per production class, mock every collaborator" is wrong by default. Walk the choice instead:

- **What information do I need from this test?** "Does this controller hand off correctly?" "Does this query method return the right rows?" Different answers want different unit sizes.
- **Default to the largest unit that doesn't require an external system.** A controller test that exercises the real service + a stubbed repository is fine — and far less brittle than three layers of class-level mocks.
- **Shrink the unit only when business logic is genuinely complex** and setup is becoming the test.
- **Stop calling tests "unit" or "integration" out of habit.** Call them what they are: "tests with no external dependencies" vs. "tests that hit a real DB / HTTP server."

---

## Test doubles — Petri's taxonomy

| Double | When to use | Distinguishing feature |
| --- | --- | --- |
| **Dummy** | A value/object is required to compile but irrelevant to the behaviour under test. | No behaviour. |
| **Stub** | The dependency is a **query** (the SUT reads from it). | Returns canned answers for expected interactions; **must throw** on unexpected ones. No verification API. |
| **Mock** | The dependency causes **side-effects** (the SUT writes to it). | Like a stub, plus a `verify()` API that asserts the expected interactions happened. |
| **Fake** | You need a lightweight working substitute (e.g. in-memory repository). | A real, simplified implementation — not for production. |
| **Spy** | You need to observe what the SUT did to the dependency without dictating responses. | Records calls/arguments; no canned responses, no `verify()`. Rarely the right choice. |

Sources: the 2022–2023 `introduction-to-{dummies,stubs,mocks,fakes,spies}` series.

---

## The canonical Spring Boot test stack (2023+)

| Concern | Tool |
| --- | --- |
| Test framework | **JUnit 5** |
| Assertions | **AssertJ** (Hamcrest only inside classic MockMvc) |
| HTTP layer test | **`MockMvcTester`** (Spring 6.2 / Boot 3.4+); classic `MockMvc` only on older versions |
| DB seeding | **Spring `@Sql`** with plain SQL scripts |
| DB assertions | **AssertJ-DB** |
| Database in CI | **Testcontainers** running the real DB image (Postgres etc.) — never H2 as a stand-in |
| HTTP doubles | **WireMock**, ideally hosted by Testcontainers |
| Mocking | **Mockito** (Java) or **MockK** (Kotlin) — manual wiring preferred for design pressure |
| Shared test setup | **JUnit 5 extensions** — never base classes, never `@Inherited` lifecycle hooks |

Source: `the-best-tools-for-writing-integration-tests-for-spring-boot-web-applications`, 2023.

### Configuring `MockMvcTester` — pick the right one

- **Standalone** (`MockMvcTester.create(mockMvc)`) — controller-only tests with stubbed services.
- **Spring context** (`MockMvcTester.from(webApplicationContext)`) with `@SpringJUnitWebConfig` — Spring MVC tests without Boot.
- **Spring Boot** (`@SpringBootTest` + `@AutoConfigureMockMvc`, constructor-inject `MockMvcTester`) — **prefer this for Boot apps.**

Use URI templates (`uri("/api/todo/{id}", 1L)`), not pre-built `java.net.URI`. Inline `.get().uri(...).exchange()` into the `assertThat(...)` call; don't store intermediates.

---

## Configuration & profiles (2024)

- Convention: two profiles, **`application`** and **`integrationTest`**. Config files: `application-application.yml`, `application-integrationTest.yml`.
- Define them as constants in a `Profiles` final class with a private constructor — string literals scattered across `@Profile` annotations rot.
- Time-dependent code uses a **profile-scoped `Clock` bean**: `Clock.systemDefaultZone()` under `application`, `Clock.fixed(...)` under `integrationTest`.
- For JDBC in integration tests, use Testcontainers' JDBC URL prefix: `jdbc:tc:postgresql:16.1:///mydb`. No manual container lifecycle code.

---

## Assertions — AssertJ idioms Petri favours

```java
assertThat(todos).hasSize(2)
    .extracting(Todo::title)
    .containsExactly("Write blog post", "Ship the PR");

assertThat(optional).isPresent().contains(expected);

assertThatThrownBy(() -> service.findById(UNKNOWN_ID))
    .isExactlyInstanceOf(NotFoundException.class)
    .hasMessage("No todo item found with the id: " + UNKNOWN_ID);

assertThat(actual.getName())
    .overridingErrorMessage("Expected name %s but was %s", expected, actual.getName())
    .isEqualTo(expected);
```

For tests with multiple assertions, use soft assertions:

```java
@Test
@DisplayName("Should return the expected information of the found item")
void shouldReturnExpectedInformation(SoftAssertions s) {
    TodoItem found = service.findById(ID).get();
    s.assertThat(found.getId()).as("id").isEqualByComparingTo(ID);
    s.assertThat(found.getTitle()).as("title").isEqualTo(TITLE);
}
```

(Inject via `@ExtendWith(SoftAssertionsExtension.class)`.)

He prefers `overridingErrorMessage("...")` over `.as("...")` / `.describedAs("...")` because it replaces the failure message instead of prefixing it.

---

## Test structure & naming

- **Sentence-style `@DisplayName`** on every class, every `@Nested` class, every `@Test`. Treat the suite as executable documentation.
- **`@Nested` per method/feature, then `@Nested When...` per condition.**

```java
@DisplayName("Find todo items")
class FindTodoItemsTest {

    @Nested
    @DisplayName("When no todo items exist")
    class WhenNone {
        @Test
        @DisplayName("Should return an empty list")
        void shouldReturnEmpty() {
            assertThat(repository.findAll()).isEmpty();
        }
    }

    @Nested
    @DisplayName("When two todo items exist")
    class WhenTwo {
        // @BeforeEach seeds via @Sql, not via repository.save()
    }
}
```

- One logical concept per test. If the display name needs an "and", split.
- Don't share state via `Lifecycle.PER_CLASS` unless you really need it — one fresh instance per test keeps mock state from leaking.

---

## Test data — the seeding hierarchy

In order of preference:

1. **SQL scripts via `@Sql`** — everyone reads SQL, Spring runs them natively, column/value pairs live next to each other.
2. **Programmatic test-data generators** — small Java classes that build domain objects directly (no business logic involved).
3. **Production-code via repositories**, hidden behind a generator class — a *last* resort. Never call services or business logic to seed.

The three reasons (from his 2024 post):

- A change in unrelated production code can break dozens of tests at once.
- Changing a `create(...)` signature breaks every unrelated test class.
- Data hidden inside service calls is hard to read when a test fails.

Prefer **AssertJ-DB** over DbUnit for DB assertions — assertions stay in Java, support custom rules and soft assertions.

---

## Canonical Spring Boot integration test

```java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles(Profiles.INTEGRATION_TEST)
@Sql("/db/todo-items.sql")
@DisplayName("GET /todo-item/{id}")
class FindTodoItemTest {

    private final MockMvcTester mvc;

    @Autowired
    FindTodoItemTest(MockMvcTester mvc) {
        this.mvc = mvc;
    }

    @Nested
    @DisplayName("When the todo item is found")
    class WhenFound {

        @Test
        @DisplayName("Should return HTTP 200 with the todo item")
        void shouldReturnTodoItem() {
            assertThat(mvc.get().uri("/todo-item/{id}", 1L).exchange())
                .hasStatusOk()
                .bodyJson().extractingPath("$.title").isEqualTo("Write blog post");
        }
    }

    @Nested
    @DisplayName("When the todo item is not found")
    class WhenNotFound {

        @Test
        @DisplayName("Should return HTTP 404")
        void shouldReturnNotFound() {
            assertThat(mvc.get().uri("/todo-item/{id}", 999L).exchange())
                .hasStatus(HttpStatus.NOT_FOUND);
        }
    }
}
```

---

## Evolved positions — old advice you'll see on the blog that no longer applies

When you read older posts on the same blog, beware the following — the current advice is on the right.

| Older stance | Current stance | Year of shift |
| --- | --- | --- |
| Unit tests for every class as default | Integration/API tests first; unit tests where they add unique value | ~2019 → 2024 |
| JUnit 4 + `@RunWith(MockitoJUnitRunner.class)` | JUnit 5 + `@ExtendWith(MockitoExtension.class)` / `MockKExtension` | 2018+ |
| Classic `MockMvc` + static `andExpect(...)` + Hamcrest `jsonPath` | `MockMvcTester` + AssertJ fluent API | 2025 |
| In-memory H2 for repository integration tests | Testcontainers running the real DB image | 2023+ |
| DbUnit XML datasets | Plain SQL scripts via `@Sql` + AssertJ-DB for assertions | 2023 |
| Base test classes for shared setup | JUnit 5 extensions | 2023 (re-stated more strongly) |
| `@Mock` + `@InjectMocks` everywhere | Manual `mockk()` / constructor wiring as design pressure | 2026 |
| Roy Osherove-style `methodName_state_expected` names | Sentence-style `@DisplayName` + `@Nested When…` scenarios | 2021+ |
| Custom HTTP test plumbing | WireMock, ideally via Testcontainers | 2023 |

If a request matches an older pattern (e.g. "help me write a JUnit 4 test with `@RunWith`"), respect the codebase's reality, but offer the modern alternative as a comment-level suggestion.

---

## Pushback playbook

When the user proposes one of the following, respond with the listed one-liner and the cited post. Don't over-explain.

- **Mocking `EntityManager` / `JdbcTemplate` / a repository class**: *"Don't mock what you don't own — use Testcontainers and exercise the real query. Mocking the framework gives you a green build that lies." (`the-best-tools-for-writing-integration-tests-for-spring-boot-web-applications`)*
- **A `BaseIntegrationTest` superclass**: *"Use a JUnit 5 extension instead — inheritance ties the suite to a fragile parent." (`introduction-to-junit-5-extensions`)*
- **Seeding test data with `service.create(...)`**: *"A test must fail for only one reason. Seed with `@Sql` instead." (`3-reasons-why-we-shouldnt-initialize-our-test-data-with-production-code`)*
- **H2 standing in for Postgres**: *"H2 is a known liar. Testcontainers with the real image — it's a one-line `jdbc:tc:postgresql:...` URL." (2023)*
- **`assertEquals(expected, actual)` everywhere**: *"AssertJ. Argument order doesn't matter, error messages are better, soft assertions are one line." (2021)*
