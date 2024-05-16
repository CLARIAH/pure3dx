# Manual for admins and owners

For background, read [architecture](architecture.md) first.
There the concepts of **A** (authoring app) and **P** (publishing app) are explained.

## Access Pure3D

*   production:

    *   **P** = [editions.pure3d.eu](https://editions.pure3d.eu)
    *   **A** = [author.pure3d.eu](https://author.pure3d.eu)

*   *acceptance* (only for testing out new developments):

    *   **P** = [editions.acc.pure3d.eu](https://editions.acc.pure3d.eu)
    *   **A** = [author.acc.pure3d.eu](https://author.acc.pure3d.eu)

Both **P** and **A** let you navigate through projects and editions, and you
can jump back and forth between **P** and **A** per project en per edition,
provided that these things exist at both ends.

## The general workflow

A user that wants to create an edition has to ask permission from an admin, as follows:

1.  The user logs in;
2.  The user sends a message to an admin (this is not done within the Pure3D system);
3.  The admin creates a new, blank project and assigns the user in question to it
    as coordinator;
4.  The user, now coordinator, encounters the new project on Pure3D and creates
    a new, blank edition;
5.  The coordinator assigns editors for that edition; they must be users that
    have logged in;
6.  The editors can now write that edition: upload a model, upload media, firing up
    Voyager Story and add annotations, articles and tours;
7.  The coordinator and editor can invite reviewers (users that have logged in) to
    read the edition and give comments; commenting is done outside Pure3D;
8.  The editor can check the edition for basic sanity at all times;
9.  When an edition is publication ready, the coordinator can publish it;
    it will then appear in the **P** app in a more professional styling; there will
    also be links from this edition in **A** to its published counterpart in **P**
    and back. Note that editions and projects in **A** are accessed by URLS that
    have long, opaque MongoDB identifiers in them, while the published editions
    have simple numbers in them instead, e.g.:

    *   **A**: `https://author.pure3d.eu/edition/64eca653b1520537c7ac5b06`
    *   **P**: `https://editions.pure3d.eu/project/1/edition/1`

    A published edition is visible both in **A** and in **P**.

10. When there are mistakes after publishing, and admin or owner can unpublish the
    edition, after which it can be modified and published again;
11. When a published edition needs a revision, it is possible to create a new edition
    on the basis of the old edition: you can download the files of the edition from
    the **A** interface, and upload it into a new edition, preferably within the
    same project; there is no special logic that links the revised edition to the
    older edition; once created, the new edition is completely independent of the
    old edition, and no file sharing takes place;
12. When an edition is definitely published, it can be thrown away from the **A** app,
    it lives on in the **P** app;
13. When a published and thrown away edition needs a revision, it is
    technically possible to obtain the files of the published edition and use it as a
    starting point for the revised edition (which will be a different edition).
    However, there is nothing yet that facilitates that, a system manager has
    to locate the files where they are stored, download them, and hand them over
    to an admin or owner. This is one reason no to trhow away a published edition
    from the **A** interface too soon.

## The authoring interface

Here we describe elements on the authoring interface that support the workflow
described above.

### Acceptance or production?

The purpose of *acceptance* is to mimick *production*. But that can cause confusion.
Am I on working on acceptance or on production? There is one visual thing that
makes the difference: an orange bar:

*   *production*

    ![production](images/prod.png)

*   *acceptance*

    ![acceptance](images/acc.png)
