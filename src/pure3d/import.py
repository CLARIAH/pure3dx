import sys
import os

from control.prepare import prepare
from control.helpers.files import listFiles, listImages, readYaml


META = "meta"
PROJECTS = "projects"
EDITIONS = "editions"
WORKFLOW = "workflow"

SCENE_DEFAULT = "intro"


def importContent():
    objects = prepare(flask=False, dataDirOnly=True)

    config = objects.config
    Messages = objects.Messages
    Mongo = objects.Mongo

    dataDir = config.dataDir
    Messages.plain(logmsg=f"Data directory = {dataDir}")

    for table in (
        "meta",
        "projects",
        "editions",
        "scenes",
        "users",
        "projectUsers",
    ):
        Mongo.checkCollection(table, reset=True)

    metaDir = f"{dataDir}/{META}"
    metaFiles = listFiles(metaDir, ".yml")
    meta = {}

    for metaFile in metaFiles:
        meta[metaFile] = readYaml(f"{metaDir}/{metaFile}.yml", defaultEmpty=True)
    Mongo.execute("meta", "insert_one", dict(meta=meta))

    projectsPath = f"{dataDir}/{PROJECTS}"
    projectIdByName = {}

    with os.scandir(projectsPath) as pd:
        for entry in pd:
            if entry.is_dir():
                projectName = entry.name
                Messages.plain(logmsg=f"PROJECT {projectName}")
                projectPath = f"{projectsPath}/{projectName}"

                meta = {}
                metaDir = f"{projectPath}/meta"
                metaFiles = listFiles(metaDir, ".yml")

                for metaFile in metaFiles:
                    meta[metaFile] = readYaml(
                        f"{metaDir}/{metaFile}.yml", defaultEmpty=True
                    )

                title = meta.get("dc", {}).get("title", projectName)

                candy = {}
                candyPath = f"{projectPath}/candy"

                for image in listImages(candyPath):
                    candy[image] = True if image.lower() == "icon.png" else False

                projectInfo = dict(
                    title=title,
                    name=projectName,
                    meta=meta,
                    candy=candy,
                )

                result = Mongo.execute("projects", "insert_one", projectInfo)
                projectId = result.inserted_id if result is not None else None
                projectIdByName[projectName] = projectId

                editionsPath = f"{projectPath}/{EDITIONS}"

                with os.scandir(editionsPath) as ed:
                    for entry in ed:
                        if entry.is_dir():
                            editionName = entry.name
                            editionPath = f"{editionsPath}/{editionName}"

                            meta = {}
                            metaDir = f"{editionPath}/meta"
                            metaFiles = listFiles(metaDir, ".yml")

                            for metaFile in metaFiles:
                                meta[metaFile] = readYaml(
                                    f"{metaDir}/{metaFile}.yml", defaultEmpty=True
                                )

                            title = meta.get("dc", {}).get("title", editionName)

                            scenes = listFiles(editionPath, ".json")
                            sceneSet = set(scenes)
                            sceneCandy = {scene: {} for scene in scenes}

                            candy = {}
                            candyPath = f"{editionPath}/candy"

                            for image in listImages(candyPath):
                                (baseName, extension) = image.rsplit(".", 1)
                                if baseName in sceneSet:
                                    sceneCandy[baseName][image] = (
                                        extension.lower() == "png"
                                    )
                                else:
                                    candy[image] = (
                                        True if image.lower() == "icon.png" else False
                                    )

                            editionInfo = dict(
                                title=title,
                                name=editionName,
                                projectId=projectId,
                                meta=meta,
                                candy=candy,
                            )
                            result = Mongo.execute(
                                "editions", "insert_one", editionInfo
                            )
                            editionId = (
                                result.inserted_id if result is not None else None
                            )

                            sceneDefault = None

                            for scene in scenes:
                                default = (
                                    sceneDefault is None and scene == SCENE_DEFAULT
                                )
                                if default:
                                    sceneDefault = scene
                                sceneInfo = dict(
                                    name=scene,
                                    editionId=editionId,
                                    projectId=projectId,
                                    candy=sceneCandy[scene],
                                    default=default,
                                )
                                result = Mongo.execute(
                                    "scenes", "insert_one", sceneInfo
                                )
                                sceneId = (
                                    result.inserted_id if result is not None else None
                                )
                                sceneId

    workflowPath = f"{dataDir}/{WORKFLOW}/init.yml"
    workflow = readYaml(workflowPath, defaultEmpty=True)
    users = workflow["users"]
    projectUsers = workflow["projectUsers"]
    projectStatus = workflow["projectStatus"]

    userIdByName = {}

    for (userName, role) in users.items():
        userInfo = dict(
            name=userName,
            role=role,
        )
        result = Mongo.execute("users", "insert_one", userInfo)
        userId = result.inserted_id if result is not None else None
        userIdByName[userName] = userId

    for (projectName, isPublished) in projectStatus.items():
        Messages.plain(logmsg=f"PROJECT {projectName} published: {isPublished}")
        Mongo.execute(
            "projects",
            "update_one",
            dict(_id=projectIdByName[projectName]),
            {"$set": dict(isPublished=isPublished)},
        )

    for (projectName, projectUsrs) in projectUsers.items():
        for (userName, role) in projectUsrs.items():
            xInfo = dict(
                userId=userIdByName[userName],
                projectId=projectIdByName[projectName],
                role=role,
            )
            Mongo.execute("projectUsers", "insert_one", xInfo)


if __name__ == "__main__":
    tasks = set(sys.argv[1:])
    if "content" in tasks:
        importContent()
