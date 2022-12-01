/*eslint-env jquery*/

const uploadControls = () => {
  const finputs = $(".fileupload")

  finputs.each((i, elem) => {
    const el = $(elem)
    const saveUrl = el.attr("url")
    console.warn({ elem, el, saveUrl })

    el.change(() => {
      const theFile = el.prop("files")[0]
      console.warn("CHANGED", { theFile })

      const throbber = createThrobber(elem)
      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener(
        "progress",
        e => {
          if (e.lengthComputable) {
            const percentage = Math.round((e.loaded * 100) / e.total)
            throbber.update(percentage)
          }
        },
        false
      )
      xhr.open("POST", `${saveUrl}/${theFile.name}`)
      xhr.send(theFile)
    })
  })
}

const createThrobber = finput => {
  const throbberWidth = 64
  const throbberHeight = 6
  const throbber = document.createElement("canvas")
  throbber.classList.add("upload-progress")
  throbber.setAttribute("width", throbberWidth)
  throbber.setAttribute("height", throbberHeight)
  finput.parentNode.appendChild(throbber)
  throbber.ctx = throbber.getContext("2d")
  throbber.ctx.fillStyle = "orange"
  throbber.update = percent => {
    throbber.ctx.fillRect(0, 0, (throbberWidth * percent) / 100, throbberHeight)
    if (percent === 100) {
      throbber.ctx.fillStyle = "green"
    }
  }
  throbber.update(0)
  return throbber
}

$(() => {
  uploadControls()
})
