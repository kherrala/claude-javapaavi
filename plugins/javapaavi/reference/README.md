# reference/

This directory is intentionally **almost empty**.

The `javapaavi` plugin is built by distilling ~290 long-form posts from [petrikainulainen.net](https://www.petrikainulainen.net/blog/) into a handful of opinionated SKILL.md files. The original posts are © Petri Kainulainen and are **not** vendored into this repo.

To recreate the local corpus for a re-distillation pass, run:

```bash
python3 -m venv ../../../.venv
../../../.venv/bin/pip install beautifulsoup4 requests lxml
../../../.venv/bin/python ../../../scripts/scrape_blog.py --out ./posts
```

The `posts/` subdirectory is gitignored and must stay that way.

See the repo root `README.md` for the full refresh workflow.
