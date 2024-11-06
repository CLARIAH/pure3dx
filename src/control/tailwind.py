import re
import platform
import stat
import os
import ssl
from urllib.request import urlopen
from shutil import copyfileobj
import certifi

from .helpers import console, run
from .files import fileExists, initTree


TAILWIND_CFG = "tailwind.config.js"
TAILWIND_VERSION = "v3.3.5"

TARGETS = dict(
    amd64="{}-x64",
    x86_64="{}-x64",
    arm64="{}-arm64",
    aarch64="{}-arm64",
)


class Tailwind:
    def __init__(self, Settings):
        self.Settings = Settings
        self.install()

    def install(self):
        Settings = self.Settings
        srcDir = Settings.srcDir
        binDir = Settings.binDir
        initTree(binDir, fresh=False)
        distDirs = [Settings.partialsIn, Settings.templateDir, Settings.jsDir]

        configInPath = f"{srcDir}/{TAILWIND_CFG}"
        configOutPath = f"{binDir}/{TAILWIND_CFG}"

        osName = platform.system().lower().replace("darwin", "macos")
        assert osName in ["linux", "macos"]
        arch = platform.machine().lower()
        target = TARGETS[arch].format(osName)
        binName = f"tailwindcss-{target}"
        binPath = f"{binDir}/{binName}"

        self.binPath = binPath
        v = (
            "latest/download"
            if TAILWIND_VERSION == "latest"
            else f"download/{TAILWIND_VERSION}"
        )
        url = f"https://github.com/tailwindlabs/tailwindcss/releases/{v}/{binName}"

        if not fileExists(binPath):
            console(f"Downloading {binName} from {url} ...")
            certifi_context = ssl.create_default_context(cafile=certifi.where())

            with urlopen(url, context=certifi_context) as instream, open(
                binPath, "wb"
            ) as outfile:
                copyfileobj(instream, outfile)

            os.chmod(binPath, os.stat(binPath).st_mode | stat.S_IEXEC)
            console("done")

        if True or not fileExists(configOutPath):
            with open(configInPath) as fh:
                text = fh.read()

            contentRe = re.compile(r"""\b(content:\s*\[).*?(\],)""")

            fileSpecs = [
                (f"{distDir}/**/*." + "{html,js}") for distDir in distDirs
            ]

            fileSpecRep = ", ".join(f'"{fileSpec}"' for fileSpec in fileSpecs)

            def contentRepl(match):
                (pre, post) = match.group(1, 2)

                return f"""{pre}{fileSpecRep}{post}"""

            text = contentRe.sub(contentRepl, text)

            with open(configOutPath, "w") as fh:
                fh.write(text)

    def generate(self, verbose=False):
        """Generate the css file.

        Issues:

        The following CSS definitions are found in the content of `_dist`,
        but not in the content of `components`, `js`, and `templates`.

        We investigate these cases and explain what we do about it.

        *   `.container` `@media`
            The `container` class is triggered by the occurrence of the word
            `container` in the HTML content in one of the article files.
            This is a false positive, it was better if tailwind had not found this.
            Luckily, we loose these false positives if we generate on the basis of
            the templates.
            The `@media` definitions accompany the `container` definition.

        *   `.visible`, `fixed`, `table`, `ring`

            Each of these are analogous to `container`: if the word `visible`
            occurrs in HTML content, its CSS class definition is inserted in
            the generated CSS.

        *   `order-2,3,4,5,6,7`
            This is a case of a generated class, one of the templates contains
            `order-{{@index}}` where index varies.
            We solve this by putting
            [all possible `order-` classes](https://tailwindcss.com/docs/order)
            in the
            [safelist](https://tailwindcss.com/docs/content-configuration#safelisting-classes).

        *   `.h-4` `.w-4` `.fill-blue-700`
            This is also a case of generated classes, in many of the icon templates:

            ```
            class="
            w-{{#if twSize}}{{twSize}}{{else}}6{{/if}}
            h-{{#if twSize}}{{twSize}}{{else}}6{{/if}}
            {{#if twColor}}fill-{{twColor}}{{/if}}`
            "
            ```

            The `p3d-project` and `p3d-edition` templates define the variables
            `twSize` and `twColor` as follows:

            ```
            <a
                href="all-projects.html"
                class="flex flex-row items-center justify-start mb-2 md:mb-0"
            >
                {{>icons/iconChevronLeft isFill=true twSize="4" twColor="blue-700"}}
                All projects
            </a>
            ```

            So far, only these values (`4` resp `blue-700` are specified, to we
            add `w-4` and `h-4` and `fill-blue-700` to the
            safelist.
        """
        Settings = self.Settings
        binDir = Settings.binDir
        binPath = self.binPath
        cfgOut = f"{binDir}/{TAILWIND_CFG}"
        cssIn = Settings.cssIn
        cssOut = Settings.cssOut
        cmdLine = f"""{binPath}  -c {cfgOut} -i {cssIn} -o {cssOut}"""
        good, stdOut, stdErr = run(cmdLine)

        if verbose or not good:
            console(stdOut)
            console(stdErr)

        console(f"{'tailwind':<10} {'css':<12} {'':<24} to {cssOut}")

        return good
