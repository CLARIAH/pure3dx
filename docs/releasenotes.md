# Release 2024-12-09

There were issues with downloading projects and editions, especially when they
were large.

1.  An out-of-memory error. This was caused because the app created
    the zip files for download *in memory*.

    *Fix:* the zipfile is now created in a temporary directory.

1.  The app sent the download in one massive body.

    *Fix:* the zipfile is now streamed to the client.

1.  The request timed out, because zipping took too long.

    *Fix:* when we add files to the zip file, we do not compress glb, mp4 files etc.
    This reduces the zipping time greatly.

1.  The download fails near the end. So: the request succeeds, the server sends the
    response, but in the end the client reports that the server has dropped the
    connection.

    *Fix:* not known yet. Instead, downloads of projects/editions whose unzipped size
    exceeds 1 GB are prevented, and the user will get a warning about that.

1.  The maximum upload size is currently 500 MB.

# Release 2024-11-18

In this release we have changed the metadata schema.

The field `dc.instructionalMethod` has been removed.

Several *dc* (or pseudo *dc*) fields have been added, resulting in:

*   `title` (existing)
*   `subtitle` (new)
*   `creator` (existing)
*   `contributor` (existing)
    Voyager related data such as model, scene, articles, media)
*   `datePublished` (date of last publishing, also present if an edition has
    been unpublished)
*   `dateUnPublished` (date of last un-publishing, also present if an edition has
    been re-published)
*   `dateCreated` (registers the creation date of projects and editions)
*   `dateModified` (registers the time of last modification to the metadata, not to the
*   `abstract` (existing)
*   `description` (existing)
*   `rights.license` (new)
*   `rights.holder` (new)
*   `contact` (new)
*   `keyword` (new, values filled from previous `subject`)
*   `audience` (new, controlled vocab)
*   `funder` (new)
*   `coverage.country` (new, controlled vocab) 
*   `coverage.geo` (new, free text meant for latitude-longitude)
*   `coverage.place` (unchanged, free text meant for latitude-longitude)
*   `coverage.period` (existing, but now with controlled vocab) 
*   `coverage.temporal` (existing, but now with free text) 
*   `subject` (existing, with new contents, controlled vocab)
*   `language` (new, controlled vocab)
*   `source` (new, controlled vocab)
*   `provenance` (existing)

All these fields are valid for editions. For projects only the following fields
are valid:

*   `title`
*   `subtitle`
*   `creator`
*   `contributor`
*   `dateCreated`
*   `dateModified`
*   `abstract`
*   `description`

All date fields will be filled in by the system if the corresponding action occurs.

In order to get the metadata right for published editions, every published edition must
undergo the following actions:

1.  unpublish the edition;
1.  check and correct the metadata;
1.  republish the edition (if there are warnings/errors that can not be resolved, you may
    *force*-republish the edition.

After having treated all published editions this way, have a look at the projects
that you want to feature, and put their publication number in the `Featured Published
Projects`, using the control on the MyWork page under `Published Project`.

Then click the button `Regenerate Pages` under the featured pages to make the choice
effective.
