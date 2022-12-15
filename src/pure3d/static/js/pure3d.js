/*eslint-env jquery*/

const report = task => (jqXHR, stat, error) => {
  if (task != null) {
    console.error(stat, { error })
    flash(task, stat)
  }
}

const flash = (task, error) => {
  const msgbar = $("#msgbar")
  const stat = error || "succeeded"
  const cls = error ? "error" : "message"
  msgbar.html(`<div class="msgitem ${cls}">&lt${task}&gt; ${stat}</div>`)
}

const processHtml = (task, destElem) => html => {
  destElem.replaceWith(html)
  uploadControl(destElem)
  if (task != null) {
    flash(task)
  }
}

const fetch = (url, task, destElem, data) => {
  if (data === undefined) {
    $.ajax({
      type: "GET",
      url,
      processData: false,
      contentType: false,
      success: processHtml(task, destElem),
      error: report(task),
    })
  } else {
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url,
      data,
      processData: false,
      contentType: true,
      success: processHtml(task, destElem),
      error: report(task),
    })
  }
}

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
  const fuploads = $(".fileupload")

  fuploads.each((i, fupload) => {
    uploadControl(fupload)
  })
}

const uploadControl = fupload => {
  const fuploadEl = $(fupload)
  const saveUrl = fuploadEl.attr("saveurl")

  const finput = fuploadEl.children("input")
  const fupdate = fuploadEl.children(".upload")
  const fdelete = fuploadEl.children(".delete")

  fupdate.off("click").click(() => {
    finput.click()
  })

  fdelete.off("click").click(e => {
    const me = $(e.currentTarget)
    const deleteUrl = me.attr("deleteurl")
    fetch(deleteUrl, "delete", fupload)
  })

  finput.change(() => {
    const theFile = finput.prop("files")[0]
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
              const { content } = response

              fupload.replaceWith(content)
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
}

$(() => {
  uploadControls()
})
