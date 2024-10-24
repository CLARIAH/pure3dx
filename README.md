<img src="/logos/logo_pure3d.png" align="left"/>

# Pure3d

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/CLARIAH/pure3dx/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/CLARIAH/pure3dx)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

## About

Pure3D is an app for authoring and publishing 3D editions.

It is the outcome of the [Pure3D project](https://pure3d.eu) led by
[Susan Schreibman](https://www.maastrichtuniversity.nl/s-schreibman)
and
[Costas Papadopoulos](https://www.maastrichtuniversity.nl/cp-papadopoulos)
at Maastricht University, Netherlands.

[Pure3D](https://editions.pure3d.eu)
is hosted on
[CLARIAH](https://www.clariah.nl)
infrastructure, managed from
[KNAW/HuC](https://di.huc.knaw.nl/home-en.html).

## Contributors

*   [Kelly Schoueri](https://www.maastrichtuniversity.nl/km-gillikin-schoueri) (Maastricht)
    - key user, source of requirements
*   MM (HuC) technical oversight
*   VD (HuC) guidance for deployment on Kubernetes
*   DH (HuC) support with the Kubernetes deployment
*   LW (HuC) support with the backup solution
*   [Bas Doppen](https://pure.knaw.nl/portal/en/persons/bas-doppen) (HuC)
    styling
*   [Jamie Cope](https://github.com/gjcope) (Smithsonian)
    support for handling the Voyager 3D web viewer
*   [Dirk Roorda](https://github.com/dirkroorda) (HuC)
    architecture and most of the code

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

You can also deploy it locally, see [local-deploy](docs/local-deploy.md).

## Technical documentation

There is a lot of documentation in the
[Python docstrings of the authoring app](https://clariah.github.io/pure3dx/control/index.html)
which is the app that contains all the business logic.

## History

*   2024-05-16 Pure3D went in production

**Earlier**

A lot has been discussed, many experiments have been carried out,
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
    See also
    [cool uris](https://www.w3.org/Provider/Style/URI).

*   A 3D dataset is more than a 3D model with annotations: there is also paradata or
    supplementary material; Pure3D does not manage such data.

*   Pure3D is currently tied to the Voyager 3D Viewer, but it is desirable to be able
    to support more viewers. Even better would it be if editions made for one viewer,
    could be consumed by another viewer.
