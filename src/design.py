from control.prepare import prepare
from control.publish import Publish


def build():
    objects = prepare(design=True)

    P = Publish(objects.Settings, objects.Messages, objects.Mongo, objects.Tailwind)

    P.genPages(None, None)


if __name__ == "__main__":
    build()
