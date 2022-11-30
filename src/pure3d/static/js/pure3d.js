/*eslint-env jquery*/

const uploadControls = () => {
  const controls = $(".fileuploadc")
  const wrappers = $(".fileuploadw")

  wrappers.each((i, el) => {
    el.hide()
  })

  controls.each((i, el) => {
    const elem = $(el)
    const fid = elem.attr("fid")
    const saveUrl = elem.attr("url")
    const wrapper = $(`div[fid="${fid}"]`)
    const finput = $(`input[fid="${fid}"]`)

    el.off("click").click(() => {
      wrapper.show()
    })

    finput.change(() => {
      const theFile = finput.prop("files")[0]
      const reader = new FileReader()

      const throbber = createThrobber(finput)
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
      xhr.overrideMimeType("text/plain; charset=x-user-defined-binary")

      reader.onload = e => {
        const fileContent = e.target.result
        xhr.send(fileContent)
      }
      reader.readAsBinaryString(theFile)
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
