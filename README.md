<img src="/logos/logo_pure3d.png" align="left"/>

# Pure3d

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/CLARIAH/pure3dx/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/CLARIAH/pure3dx)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

## About

Pure3D is an app for authoring and publishing 3D editions.

It is the outcome of the [Pure3D project](https://pure3d.eu) led by
Susan Schreibman and Costas Papadopoulos at Maastricht University, Netherlands.

[Pure3D](https://editions.acc.pure3d.eu)
is hosted on CLARIAH infrastructure, managed from
[KNAW/HuC](https://di.huc.knaw.nl/home-en.html).

## Contributors

*   Kelly Schoueri (Maastricht) - key user, source of requirements
*   MM (HuC) - technical oversight
*   VD (HuC) - guidance for deployment on Kubernetes
*   DH (HuC) - support with the Kubernetes deployment
*   LW (HuC) - support with the backup solution
*   Bas Doppen (HuC) - styling
*   Jamie Cope (Smithsonian) - support for handling the Voyager 3D web viewer
*   [Dirk Roorda](https://github.com/dirkroorda) (HuC)
    - architecture and most of the code

## Components

Pure3D consists of two parts:

*   an authoring app, where users can create 3D editions and publish them;
*   a publishing app, showing the published editions as static web pages.

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
[Kubernetes cluster for CLARIAH](https://code.huc.knaw.nl/pure3d/pure3d-config)
at the HuC.

## Technical documentation

There is a lot of documentation in the
[Python docstrings of the authoring app](https://clariah.github.io/pure3dx/control/index.html)
which is the app that contains all the business logic.

## History

In the earlier stages a lot has been discussed, many experiments have been carried out,
great whishes have been expressed. It is still visible in a
[previous repo](https://github.com/CLARIAH/pure3d).

## Missing bits

Not everything that we had in mind has been implemented so far. There is much room
for improvements and further development:

*   The layout of the authoring app is unpolished and primitive. It should look
    more like the layout of the publishing app.

*   The handling of metadata is not sophisticated: just a few Dublin Core fields with
    unconstrained content.

*   Search has not been implemented, not in the authoring app and not in the publishing
    app.

*   Pre-flight checks for publication are basic: checks for broken links and
    unreferenced files. It should also check for completeness of metadata.

*   No attempt for persistent identifiers has been made; we do have stable urls for
    published editions: `https://editions.pure3d.eu/project/p/edition/e` where `p` and
    `e` are the project and edition numbers, which start at `1`.

*   A 3D dataset is more than a 3D model with annotations: there is also paradata or
    supplementary material; Pure3D does manage such data.

*   Pure3D is currently tied to the Voyager 3D Viewer, but it is desirable to be able
    to support more viewers. Even better would it be if editions made for one viewer,
    could be consumed by another viewer.
