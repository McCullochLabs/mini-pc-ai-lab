# Repository rename review

Proposed repository name is `McCullochLabs/ai-hardware-lab`. Suggested repository description is “Independent, reproducible hardware testing for real-world local AI development.”

- The reviewed baseline has no GitHub Actions workflow, reusable action, Pages source/configuration, badges or GitHub templates. Relative documentation links work under either slug. The branding review updates the original proposed diagram.
- Before rename, confirm target slug availability under an authorized account and inspect repository settings for Pages, webhooks, installed apps and deployment integrations. Settings and external consumers were outside the inspected source tree.
- If Pages is enabled, map the project-site URL and inbound links, and confirm any custom-domain configuration. Search external workflow consumers for actions invoked by old slug and migrate if applicable. GitHub does not redirect action calls.
- Inventory external profile links, shared documents and outreach links. After an approved rename, update local Git remotes and any automation, webhook consumers, raw-file references and external links that use the old name. Avoid reusing the old slug because it breaks GitHub redirects.
- After the rename, verify the canonical repository, old repository redirect, clone/fetch, links, any Pages deployment and integration events. Repository rename and metadata changes are separate owner-approved operations.

See [GitHub’s repository rename documentation](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository).
