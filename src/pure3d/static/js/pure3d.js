/*eslint-env jquery*/

const addMsg = (tp, msg, replace = false) => {
  const msgbar = $("#msgbar")
  const html = `<span class="msgitem ${tp}">${msg}</span>`
  if (replace) {
    msgbar.html(html)
  } else {
    msgbar.append(html)
  }
}

window.addMsg = addMsg

const uploadControls = () => {
  const finputs = $(".fileupload")

  finputs.each((i, elem) => {
    const el = $(elem)
    const saveUrl = el.attr("url")
    const fid = el.attr("fid")
    const show = el.attr("show")

    el.change(() => {
      const theFile = el.prop("files")[0]
      const xhr = new XMLHttpRequest()
      const { upload } = xhr

      const stat = { problem: false, success: false, processed: false }

      const handleEvent = e => {
        const { type } = e

        if (type == "error" || type == "abort" || type == "timeout") {
          stat.problem = true
          addMsg("error", "uploading failed", true)
        } else if (type == "load" || type == "loadend") {
          if (!stat.success) {
            addMsg("info", "done uploading ...", true)
            if (!stat.problem) {
              stat.success = true
            }
          }
        } else if (type == "readystatechange") {
          if (stat.success) {
            if (!stat.processed) {
              const { response } = xhr
              if (response) {
                addMsg("good", "uploaded", true)
                const { staticUrl } = response

                if (show != null) {
                  const elem = $(`img[fid="${fid}"]`)
                  elem.attr("src", `${staticUrl}?v=${new Date().getTime()}`)
                }
                stat.processed = true
              }
            }
          }
        } else {
          addMsg("info", "still uploading ...", true)
        }
      }

      upload.addEventListener("loadstart", handleEvent)
      upload.addEventListener("load", handleEvent)
      upload.addEventListener("loadend", handleEvent)
      upload.addEventListener("progress", handleEvent)
      upload.addEventListener("error", handleEvent)
      upload.addEventListener("abort", handleEvent)
      upload.addEventListener("timeout", handleEvent)
      xhr.addEventListener("readystatechange", handleEvent)

      xhr.responseType = "json"
      xhr.open("POST", `${saveUrl}/${theFile.name}`)
      xhr.send(theFile)
    })
  })
}

$(() => {
  uploadControls()
})
