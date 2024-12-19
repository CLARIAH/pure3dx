<img src="/logos/logo_pure3d.png" align="left"/>

# Pure3d

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/CLARIAH/pure3dx/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/CLARIAH/pure3dx)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

## About

Pure3D is an app for authoring and publishing 3D editions.
It is the outcome of the
[Pure3D project](https://pure3d.eu/)
led by
[Costas Papadopoulos](https://www.maastrichtuniversity.nl/cp-papadopoulos)
at Maastricht University, Netherlands.

[Pure3D](https://editions.pure3d.eu)
is hosted on
[CLARIAH](https://www.clariah.nl)
infrastructure, managed from
[KNAW/HuC](https://di.huc.knaw.nl/home-en.html).

## Contributors

The Maastricht University project team
consists of

*   Susan Schreibman (Co-PI),
*   [Kelly Gillikin Schoueri](https://www.maastrichtuniversity.nl/km-gillikin-schoueri)
    (Ph.D. researcher),
*   Alicia Walsh (Research Assistant),
*   Sohini Mallick (Research Software Engineer).

Project partners include the

*   4DRLab at the University of Amsterdam,
*   KNAW Humanities Cluster - Digital Infrastructure,
*   Data Archiving and Networked Services (DANS).

Pilot projects through which user requirements have
been developed are contributed by

*   4DRLab,
*   Erfgoed Leiden en Omstreken,
*   Gemeente Maastricht,
*   Museum van Bommel van Dam,
*   Nederlands Mijnmuseum.

The software in this repo the product of

*   [Bas Doppen](https://pure.knaw.nl/portal/en/persons/bas-doppen):
    visual design of the editions app;
*   [Dirk Roorda](https://github.com/dirkroorda):
    the code: backend, integration, and the overall architecture;
*   Qiqing Ding (Vic) and his colleagues in the Concern Infrastructure team:
    lots of help on the containerization and Kubernetes deployment;
*   Pure3D contains several releases of the
    [Smithsonian Voyager](https://github.com/Smithsonian/dpo-voyager),
    whose main developer is
    [Jamie Cope](https://github.com/gjcope) who provided helpful support
    for handling the Voyager 3D web viewer within Pure3D.

## Components

Pure3D consists of two parts:

*   (**A**) an authoring app, where users can create 3D editions and publish them;
*   (**P**) a publishing app, showing the published editions as static web pages.

Both parts make use of the
[Smithsonian Voyager](https://github.com/Smithsonian/dpo-voyager)
as 3D-viewer for the web with facilities for enrichments and annotations.

For more detail, see
[architecture](docs/architecture.md).

## Manual

There is a concise manual for admin/owners of the Pure3D system
[here](docs/manual-admin.md).

## Deployment

Pure3D is deployed on a
[Kubernetes](https://kubernetes.io/docs/home/)
cluster for CLARIAH at the HuC.
The important thing to know is that the **P** and **A** app have their own deployments
with their own pods and containers. They can run independently.
So, if **A** fails for some reason, **P** happily prods along, and vice versa.

This whole setup is duplicated into a production cluster and a development cluster.
In the production cluster there is an extra deployment that takes care of an incremental
backup with a retention of 30 days.

For more information on the set up you need to have a VPN connection to the HuC
institute and then you can follow this
[link](https://code.huc.knaw.nl/pure3d/pure3d-config).

You can also deploy it locally, see [local-deploy](docs/local-deploy.md). Also for that
you need to fetch information that is only accessible over the VPN to the HuC.

## Technical documentation

There is a lot of documentation in the
[Python docstrings of the authoring app](https://clariah.github.io/pure3dx/control/index.html)
which is the app that contains all the business logic.

## Design development

The [design guide](docs/design.md) describes the ins and outs of developing the design
op the published pages.

## History

*   2024-05-19 Moved location for temp files off the data volume to a new temp volume,
    which is excluded from backup.
*   2024-05-16 Pure3D went in production.
*   2024-12-10 Improvements in metadata handling and visual design.

**Earlier**

A lot has been discussed, many experiments have been carried out,
great whishes have been expressed. It is still visible in a
[previous repo](https://github.com/CLARIAH/pure3d).

## Missing bits

Not everything that we had in mind has been implemented so far. There is much room
for improvements and further development:

*   The layout of the authoring app is unpolished and very different from the layout
    of the published editions.

*   The handling of metadata is not sophisticated: just a few Dublin Core
    fields, most with unconstrained content, and some with controlled vocabularies.

*   Search has not been implemented, not in the authoring app and not in the publishing
    app.

*   Pre-flight checks for publication are basic: checks for broken links and
    unreferenced files and presence of metadata. More checks, especially on the
    metadata, would be helpful.

*   No attempt for persistent identifiers has been made; we do have stable urls for
    published editions: `https://editions.pure3d.eu/project/p/edition/e` where `p` and
    `e` are the project and edition numbers, which start at `1`.
    See also
    [cool uris](https://www.w3.org/Provider/Style/URI).

*   A 3D dataset is more than a 3D model with annotations: there is also paradata or
    supplementary material; Pure3D does not manage such data.

*   Pure3D is currently tied to the Voyager 3D Viewer, but it is desirable to be able
    to support more viewers. Even better would it be if editions made for one viewer,
    could be consumed by another viewer. But that presupposes more interoperability
    between viewers, especially where it comes to annotation, than is currently the
    case.
