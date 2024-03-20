import sys

from control.prepare import prepare
from control.static import Static as StaticCls


def build(featured):
    objects = prepare(design=True)

    Static = StaticCls(
        objects.Settings,
        objects.Messages,
        objects.Viewers,
        objects.Tailwind,
        objects.Handlebars,
    )

    Static.genPages(None, None, featured)


if __name__ == "__main__":
    build(sys.argv[1:])
