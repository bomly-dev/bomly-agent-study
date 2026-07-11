# Attribution

This directory vendors **Internet2 Grouper** (https://github.com/Internet2/grouper),
an open-source access-management / group-management system, pinned at a
historical commit on its 4.x line: branch `GROUPER_4_BRANCH`, commit
`6c294076be12f513dda370d3d6ee987c9d40d690`.

- Upstream license: Apache License 2.0 (see `LICENSE.txt` in this directory).
- Copyright: Internet2 and the Grouper contributors.

## Why it is here, and what was changed

This is a research fixture in a dependency-remediation study: the application is
used **as it existed at this historical commit**, including its multi-module
Maven dependency tree from that point in time. Nothing about the application
code, any `pom.xml`, or any dependency version has been modified. Newer upstream
releases exist; do not treat this copy as current Grouper, and do not report
findings about this copy to the Grouper project.

This is the study's **large multi-module** fixture (`bigapp`): a 13-module Maven
reactor rooted at `grouper-parent/`, with a much larger vulnerable dependency
surface than the other fixtures — the regime where whole-graph vulnerability
intelligence is expected to matter.

Local changes, for the study only:
- this `ATTRIBUTION.md` file was added;
- removed content that plays no role in building or scanning the reactor, to
  keep the vendored size manageable: generated Javadoc (`**/doc/api/`),
  JavaScript source maps (`*.map`), and the non-reactor connector / proof-of-
  concept modules that are not referenced by `grouper-parent` and only carried
  large bundled jars (`grouper-misc/grouperAtlassianConnector`,
  `grouper-misc/grouperKimConnector`, `grouper-misc/poc_*`,
  `grouper-misc/grouper.client-*`). The 13 reactor modules and their sources
  are intact.

The reactor is built (`mvn -DskipTests install` from `grouper-parent/`) at image
build time so its internal modules resolve; tests are not run for this fixture
(compile + scan only).
