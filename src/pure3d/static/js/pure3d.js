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

const addMsgs = (messages, replace = false) => {
  const msgbar = $("#msgbar")
  if (replace) {
    msgbar.html("")
  }
  for (const message of messages) {
    const [tp, msg] = message
    const html = `<span class="msgitem ${tp}">${msg}</span>`
    msgbar.append(html)
  }
}

window.addMsg = addMsg
window.addMsgs = addMsgs

const report = task => (jqXHR, stat) => {
  if (task != null) {
    addMsg("error", `${task} ${stat}`)
  }
}

const processHtml = (task, destElem) => response => {
  console.warn(task, response, { fupload: destElem })
  const { status: stat, messages, content } = response
  if (stat) {
    const destElemJQ = $(destElem)
    destElemJQ.html(content)
    uploadControl(destElem)
    if (task != null) {
      addMsg("good", `${task} succeeded`, true)
    }
  }
  else {
    console.warn({ stat, messages })
    addMsgs(messages)
  }
}

const fetchData = (url, task, destElem, data) => {
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

const uploadControls = () => {
  const fuploads = $(".fileupload")

  fuploads.each((i, fupload) => {
    uploadControl(fupload)
  })
}

const uploadControl = fupload => {
  const fuploadJQ = $(fupload)
  const saveUrl = fuploadJQ.attr("saveurl")

  const finput = fuploadJQ.find("input")
  const fupdate = fuploadJQ.find("span.upload.button")
  const fdelete = fuploadJQ.find("span.delete.button")

  fupdate.off("click").click(() => {
    finput.click()
  })

  fdelete.off("click").click(e => {
    const eJQ = $(e.currentTarget)
    const deleteUrl = eJQ.attr("url")
    fetchData(deleteUrl, "delete", fupload)
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
          addMsg("good", "uploaded.", true)
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

              console.warn("UPLOADED", { content, fupload })
              fuploadJQ.html(content)
              uploadControl(fupload)
              stat.processed = true
            }
          }
        }
      } else {
        addMsg("info", "still uploading ...")
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
