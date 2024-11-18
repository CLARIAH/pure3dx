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
