# Pure3d system architecture

Pure3D is an app to create 3D editions and to publish them.

We have separated Pure3D into an
[authoring app](https://author.pure3d.eu) (**A**)
and a
[publish app](https://author.pure3d.eu) (**P**)

There are very few dependencies between the two.

The **P** can be deployed without the presence of (**A**), and this is important,
because **P** must be able to work into the indefinite future.
That is why **P** is very simple: it is an out-of-the-box NGINX webserver that
serves a directory of static pages. Very easy to maintain.

In **P** there is no user management, no login functionality, no underlying database,
no dynamic generation of web pages.

The content that **P** serves comes from **A**, when users press the `Publish` button.
This is a complex app, that deals with users and their authentication and authorisation
to do various operations.

Note that the generation of static pages for an edition when it gets published, is not
performed by **P**, but by **A**. This helps to keep **P** really dumb.

![diagram](images/pure3d-system.png)
