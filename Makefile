.PHONY: site help deploy

help:
	@echo "Targets:"
	@echo "  make site  - regenerate the experience timeline in index.html"
	@echo "               from resume-generator/data/experience.yaml"
	@echo "  make deploy FILES=\"word-bubbles index.html\" - upload to shrenp.com over SSH (-n via scripts/deploy.sh for a dry run)"

# Runs render_site.py inside the resume-generator uv environment so it
# can import resume_generator.models without a separate install.
site:
	uv run --project resume-generator python scripts/render_site.py

deploy:  ## upload paths to shrenp.com, e.g. make deploy FILES="word-bubbles index.html"
	scripts/deploy.sh $(FILES)
