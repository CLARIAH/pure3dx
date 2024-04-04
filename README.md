# Pure3dx

## About

Pure3D is an app for authoring and publishing 3D editions.

It is the outcome of the [Pure3D project](https://pure3d.eu) lead by
Susan Schreibman and Costas Papadopoulos at Maastricht University, Netherlands.

Pure3D is hosted on CLARIAH infrastructure, managed from
[KNAW/HuC](https://di.huc.knaw.nl/home-en.html).

## Contributors

*   Kelly Schoueri (Maastricht) - key user, source of requirements
*   MM (HuC) - technical oversight
*   VD (HuC) - guidance for deployment on Kubernetes
*   DH (HuC) - support with the Kubernetes deployment
*   Bas Doppen (HuC) - styling
*   Jamie Cope (Smithsonian) - support for handling the Voyager 3D web viewer
*   Dirk Roorda (HuC) - architecture and most of the code

## Components

Pure3D consists of two parts:

*   an authoring app, where users can create 3D editions and publish them;
*   a publishing app, showing the published editions as static web pages.

Both parts make use of the
[Smithsonian Voyager](https://github.com/Smithsonian/dpo-voyager)
as 3D-viewer for the web with facilities for enrichments and annotations.

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

*   the layout of the authoring app is unpolished and primitive. It should look
    more like the layout of the publishing app;
*   the handling of metadata is not sophisticated: just a few Dublin Core fields with
    unconstrained content;
*   search has not been implemented, not in the authoring app and not in the publishing
    app;
*   pre-flight checks for publication are basic: checks for broken links and
    unreferenced files. It should also check for completeness of metadata;
*   no attempt for persistent identifiers has been made; we do have stable urls for
    published editions: `https://editions.pure3d.eu/project/p/edition/e` where `p` and
    `e` are the project and edition numbers, which start at `1`;
*   a 3D dataset is more than a 3D model with annotations: there is also paradata or
    supplementary material; Pure3D does manage such data.
