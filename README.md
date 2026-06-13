# javapaavi — a Claude Code plugin

> An opinionated Java / Spring Framework / automated-testing collaborator. Modelled on the writing of Petri Kainulainen ([petrikainulainen.net](https://www.petrikainulainen.net/blog/)).

`javapaavi` ("Java Petri" in Finnish) is a single-plugin Claude Code marketplace that distils ~290 long-form blog posts into a compact, opinionated coding agent. It ships:

- one **agent** — `javapaavi`, an old-school senior Java engineer with strong, well-defended opinions on testing, Spring, and clean code;
- five **skills** that practise what he preaches:
  - `automated-testing` — JUnit 5, AssertJ, MockMvcTester, Testcontainers, test doubles, test data builders.
  - `spring-framework` — Spring Boot, Spring Data JPA, Spring MVC, profiles, DTOs vs entities, transactions.
  - `java-programming` — Java idioms, domain modelling, builders, Maven/Gradle hygiene.
  - `software-architecture` — the three-layer (web → service → repository) reference architecture, layer boundaries, the anaemic-domain-model flaw, DDD building blocks, monolith vs microservices/SOA, reusability/YAGNI, Just-Enough-Up-Front design.
  - `convention-audit` — autonomous or interactive project audit against the four skills above (conventions **and** architecture). Interactive mode asks clarifying questions in the **Savo dialect of Finnish**.

The agent will push back politely but firmly on field injection, leaky entities, mocked databases, and tests that assert on framework behaviour.

## Install

### Quick install (scripts)

If you have the `claude` CLI on your PATH, the helper scripts do the marketplace
add + plugin install for you:

```
./scripts/setup.sh              # install from GitHub
./scripts/setup.sh --local      # install from this checkout (local development)
./scripts/upgrade.sh            # pull the latest version
./scripts/uninstall.sh          # remove the plugin and its marketplace
```

After any of these, **run `/reload-plugins` in a running Claude Code session**
(or restart it) to apply the change. Verify with `claude plugin list`.

### Manual install (slash commands)

This repo is structured as a Claude Code marketplace. From any Claude Code session:

```
/plugin marketplace add kherrala/claude-javapaavi
/plugin install javapaavi@javapaavi-marketplace
/reload-plugins
```

To install a specific version once a tag exists:

```
/plugin marketplace add kherrala/claude-javapaavi@v0.2.0
```

To uninstall:

```
/plugin uninstall javapaavi
/plugin marketplace remove javapaavi-marketplace
/reload-plugins
```

## What you can ask it

After installing, drop into a Java/Spring project and try things like:

```
> /agents javapaavi  — write me a Spring Data JPA repository for a TodoItem,
  with a search method and an integration test.

> Audit this project for javapaavi conventions.        # autonomous mode

> Tee javapaavi-auditointi, kyselle savoks.            # interactive (Savo) mode

> Refactor this controller to follow javapaavi's DTO-at-the-boundary rule.

> Why is my @MockBean(EntityManager) wrong?            # he'll explain, politely.
```

## How it's structured

```
.
├── .claude-plugin/
│   └── marketplace.json          # marketplace manifest (install entry point)
├── plugins/
│   └── javapaavi/
│       ├── .claude-plugin/
│       │   └── plugin.json       # plugin manifest
│       ├── agents/
│       │   └── javapaavi.md      # the persona agent
│       ├── skills/
│       │   ├── automated-testing/SKILL.md
│       │   ├── spring-framework/SKILL.md
│       │   ├── java-programming/SKILL.md
│       │   ├── software-architecture/SKILL.md
│       │   └── convention-audit/SKILL.md
│       └── reference/
│           └── README.md         # explains why the corpus is NOT in this repo
├── scripts/
│   ├── setup.sh                  # install the plugin via the claude CLI
│   ├── upgrade.sh                # update an installed plugin
│   ├── uninstall.sh              # remove the plugin + marketplace
│   ├── scrape_blog.py            # download the blog (does NOT commit to repo)
│   └── refresh.sh                # convenience wrapper: scrape + re-distill prompt
├── LICENSE
├── NOTICE
└── README.md
```

## Refreshing the distillation

The skills shipped with this plugin are **distilled** from blog content; the original posts themselves are **deliberately not vendored** in this repo (Petri Kainulainen retains copyright on his prose). To update the skills against the latest posts:

```bash
# 1. Set up the scraper environment
python3 -m venv .venv
.venv/bin/pip install beautifulsoup4 requests lxml

# 2. Pull the latest posts into a gitignored local cache
.venv/bin/python scripts/scrape_blog.py --out plugins/javapaavi/reference/posts

# 3. Open this repo in Claude Code and ask:
#    "Refresh the five javapaavi skills from the reference/ corpus,
#     biasing toward post-2022 content and noting where his thinking has
#     evolved."
```

The `reference/posts/` directory is in `.gitignore` and must stay that way.

## A note on dated advice

The blog runs from 2010 to 2026. Older posts (notably the 2012–2015 Spring Data JPA tutorial series) predate Spring Boot auto-configuration, use XML config, and assume JUnit 4 + Hamcrest. The skills bias toward Petri's *current* stance (post-2022: Spring Boot 3.x, JUnit 5, AssertJ, MockMvcTester, Testcontainers) and explicitly call out where his recommendation has evolved.

If you spot the agent recommending something dated, open an issue or send a PR — the skill files are plain markdown.

## Licensing & attribution

The entire repository is licensed under **Apache License 2.0** — matching the license Petri Kainulainen applies to the code samples on his blog. One license everywhere, no boundary friction.

- See `LICENSE` for the full Apache-2.0 text.
- See `NOTICE` for the attribution statement covering blog-derived content.

The original blog posts themselves are © Petri Kainulainen and are **not vendored** in this repo. The scraper pulls them to a `.gitignored` local cache only when you choose to re-distill the skills.

Petri Kainulainen is not affiliated with this plugin and has not endorsed it. The plugin's recommendations are our paraphrase of his stated opinions, not direct quotation, and any error is ours. If Petri or his representatives would prefer different terms, please open an issue and I will revise or remove.

## Acknowledgements

Built on top of more than fifteen years of Petri Kainulainen's writing. Any wisdom in this plugin is his; any over-confident misreading of it is mine.
