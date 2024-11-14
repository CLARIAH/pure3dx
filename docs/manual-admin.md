# Manual for admins and owners and devops

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

The life cycle of an edition starts with somebody that wants to create an edition.

1.  The user logs in.
2.  The user sends a message to an admin (this is not done within the Pure3D system).
3.  The admin creates a new, blank project and assigns the user in question to it
    as organiser.
4.  The user, now organiser, encounters the new project on Pure3D and creates
    a new, blank edition.
5.  The organiser assigns editors for that edition; they must be users that
    have logged in.
6.  The editors can now write that edition: upload a model, upload media, firing up
    Voyager Story and add annotations, articles and tours.
7.  The organiser and editor can invite reviewers (users that have logged in) to
    read the edition and give comments; commenting is done outside Pure3D.
8.  The editor can check the edition for basic sanity at all times.
9.  When an edition is publication ready, the organiser can publish it;
    it will then appear in the **P** app in a more professional styling; there will
    also be links from this edition in **A** to its published counterpart in **P**
    and back. Note that editions and projects in **A** are accessed by URLS that
    have long, opaque MongoDB identifiers in them, while the published editions
    have simple numbers in them instead, e.g.:

    *   **A**: `https://author.pure3d.eu/edition/64eca653b1520537c7ac5b06`
    *   **P**: `https://editions.pure3d.eu/project/1/edition/1`

    A published edition is visible both in **A** and in **P**.

10. When there are mistakes after publishing, and admin or owner can unpublish the
    edition, after which it can be modified and published again.
11. When a published edition needs a revision, it is possible to create a new edition
    on the basis of the old edition: you can download the files of the edition from
    the **A** interface, and upload it into a new edition, preferably within the
    same project; there is no special logic that links the revised edition to the
    older edition; once created, the new edition is completely independent of the
    old edition, and no file sharing takes place.
12. When an edition is definitely published, it can be thrown away from the **A** app,
    it lives on in the **P** app.
13. When a published and thrown-away edition needs a revision, it is
    technically possible to obtain the files of the published edition and use them as a
    starting point for the revised edition (which will be a different edition).
    However, there is nothing yet that facilitates that, a system manager has
    to locate the files where they are stored, download them, and hand them over
    to an admin or owner. This is one reason not to throw away a published edition
    from the **A** interface too soon.

## The authoring interface

Here we describe elements on the authoring interface that support the workflow
described above.

### Acceptance or production?

The purpose of *acceptance* is to mimick *production*. But that can cause confusion.
Am I on working on acceptance or on production? There is one visual thing that
makes the difference: an orange bar:

*   *production*

    <img src="images/prod.png" width="600">

*   *acceptance*

    <img src="images/acc.png" width="600">

### My work

The most straightforward entry-point to start working is the `My Work` button.
Depending on who you are, the app shows you the things you can do. Here we focus
on what you see if you are an admin or owner.

You see the sections:

*   My details
*   My projects and editions
*   Published projects
*   All projects and editions
*   Manage users

We'll discuss them one by one.

#### `My details`

<img src="images/mydetails.png" width="750">

Here you see who you are, according to the system, and in particular, what role
you have. You can change your role, provided you are an admin or owner:
you can demote yourself. You cannot promote yourself, unless there are no owners
or admins in the system. Then you can make yourself owner or admin.
In this way, you can make somebody owner or admin of a new system without asking
the system manager to do so.

Note that once you demote yourself, you cannot promote yourself again, in general.
You'll have to ask somebody with a more powerful role to promote you.
If nobody has a more powerful role, then you can promote yourself.

#### `My projects and editions`

Users have two kind of roles:

*   *general* roles such as `owner`, `admin`, `user`, `guest`;
*   *special* roles such as `organiser`, `editor`, `reviewer`; users have these roles
    with respect to particular projects and editions;

<img src="images/myprojecteditions.png" width="750">

Under this tab, the projects/editions are listed for which you have a *special* role.

Here you can add other people in specific roles to your projects and editions,
depending on your own role. Organizers can add editors to editions,
organizers and editors can add reviewers to editions.

#### `Published projects`

Projects that have published editions are visible themselves.
We call them published projects, although they may contain editions that are not yet
published.

<img src="images/publishedprojects.png" width="600">

What you see here is not a list of published projects, but some controls to do something
to the published projects.

First of all, here is where you can determine which projects are *featured*.
Featured projects will be shown on the home page of the **P** app.

Every project in the **P** app has a number, it is the number you see in the
URL after `project`:

```
https://editions.pure3d.eu/project/7/index.html
```

Secondly, you can regenerate the HTML pages for the **P** app. When is this needed?

If you have changed the featured projects. It will only take effect after regeneration.

Also, the systems manager has to do it when the **P** app gets a new layout.
Then the HTML for everything in the **P** app has to be regenerated.

#### `All projects and editions`

Here is an overview of all projects and editions in the system.

It is very much like `My projects and editions`, except that you also see
the projects and editions for which you have no special role.
Normal users do not see this section, whereas they do see the `My projects and editions`
section.

You can give users special roles with respect to projects and editions here.
In particular, if you have created a new project, you'll find that project here and you
can assign an organiser to it. That will set off the authoring of a new edition.

#### `Manage users`

<img src="images/manageusers.png" width="750">

Here you can see all users in the system that have been authenticated.

The thing to do here is to give them general roles. You do not have to do this often,
because all new users have role `user` by default.
Only when you want to promote or demote users you want to take action here.

If you do not trust a user and want to give him less rights, you can change his role
to `guest`, which gives the same rights as an unauthenticated user.

Conversely, here you can make other users admin. If you are an owner yourself, you
can make other users owner as well.

### Edition pages

An edition page has additional controls for checking, publishing and unpublishing.

If you are an organiser, you see the `check` and `publish` controls.

If you are an owner or admin, and the edition is published, you see the `unpublish`
control.

If you are both admin/owner and organiser, you see all controls.

These controls are in the left column:

<img src="images/publishcontrols.png" width="750">

Here is what you see (from top to button):

*   a link to the published counterpart in the **P** interface;
*   a button to check the edition;
*   a button to publish (again);
*   a button to *force* publish (again) - even if the checking process revealed errors;
*   a button to unpublish.

The checking process does more than checking only: it produces a bunch of overviews,
you find them in the right column, under **Scene overview**:

<img src="images/publishoverviews.png" width="750">

Here is what you see (from top to button):

*   a collapsible view on the `scene.svx.json` file. If that file contains links to
    non-existing files, they will be colored red. In this case, we see that there are
    such links. This site must have been published with *force*.
    You can expand triangles until you see exactly where the culprits are.

    <img src="images/culprits.png" width="500">

*   **Table of models**

    All 3D models plus information which files reference them and how often.

    <img src="images/tablemodels.png" width="600">

*   **Table of articles**

    All authored articles plus information which files reference them and how often.

    <img src="images/tablearticles.png" width="600">

*   **Table of media**

    All added media files plus information which files reference them and how often.
    The media files that are not used are marked with a warning color.

    <img src="images/tablemedia.png" width="650">

*   **Table of link(s) with missing target**

    All files with links that point to within the edition but not to something that
    exists there. External links are not checked.

    <img src="images/tablelinks.png" width="650">


### Pre-flight checking

Editors should use the `check` button before publishing and then check the coloured
items in these overviews. Probably they can do something about it:

*   remove unused media files;
*   correct broken links, either by editing the link itself, of by renaming or adding 
    the file that is the target of the link.

## Set up a new instance (devops)

When a new instance of Pure3D is set up, and you start with a new database, it might
be desirable to populate sets of keywords that are associated with certain
metadata fields, e.g. periods, countries, languages, subjects, licences. 

An initial set is stored in the yaml file *keywords.yml* and you can import it by 
means of a shell command.
No exisiting keywords will be deleted, the initial keywords will be added to
the existing ones.

Note that once imported, admins may add/delete keywords to the keywords table.
When you re-import the initial set, no keywords will be deleted, so the later additions
will be preserved, but all deleted keywords of the initial set will reappear.

When you do it in a local version of the app, make sure the container for moongodb
of the app is running:

```
k
kset pure3d author
```

```
k
kset pure3d author
kcd
cd src
./initkeywords.sh --dry pilot
```

(or instead of `pilot`: `test` or `custom` or `prod`).

You'll see roughly what the effect of merging in the initial keywords will be.

If all looks good, you can perform the action, by omitting the `--dry` argument:

```
./initkeywords.sh pilot
```

To check whether you really have the keywords, run it again with or without `--dry`
(the operation is idempotent). You see that there are many keywords in the system now
and that none has to be added.

For the production and acceptance systems:

```
k
kset pure3d mongodb
ksh
```

You are now in a shell on the remote server.

```
cd src
./initkeywords.sh --dry pilot
./initkeywords.sh pilot
./initkeywords.sh --dry pilot
```

