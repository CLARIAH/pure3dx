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

const processUploads = (task, destElem) => response => {
  const { status: stat, messages, content } = response
  if (stat) {
    const destElemJQ = $(destElem)
    destElemJQ.html(content)
    uploadControl(destElem)
    if (task != null) {
      addMsg("good", `${task} succeeded`, true)
    }
  } else {
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
      success: processUploads(task, destElem),
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
      success: processUploads(task, destElem),
      error: report(task),
    })
  }
}

const editWidgets = () => {
  $(".editcontent").hide()
  $(`a.button[kind="cancel"]`).hide()
  $(`a.button[kind="return"]`).hide()
  $(`a.button[kind="reset"]`).hide()
  $(`a.button[kind="save"]`).hide()
  $(`.editwidgets`).hide()
  const editwidgets = $(".editwidget")

  editwidgets.each((i, editwidget) => {
    editWidget(editwidget)
  })
}

const handleTyping = (buttons, container) => () => {
  const { cancelButton, returnButton, resetButton, saveButton } = buttons
  const value = container.val()
  const origValue = container.attr("origvalue")
  if (origValue == value) {
    cancelButton.hide()
    returnButton.show()
    resetButton.hide()
    saveButton.hide()
  } else {
    cancelButton.show()
    returnButton.hide()
    resetButton.show()
    saveButton.show()
  }
}

const editWidget = editwidget => {
  const editwidgetJQ = $(editwidget)
  const updateButton = editwidgetJQ.find(`a.button[kind="update"]`)
  const cancelButton = editwidgetJQ.find(`a.button[kind="cancel"]`)
  const returnButton = editwidgetJQ.find(`a.button[kind="return"]`)
  const resetButton = editwidgetJQ.find(`a.button[kind="reset"]`)
  const saveButton = editwidgetJQ.find(`a.button[kind="save"]`)
  const editContent = editwidgetJQ.find(".editcontent")
  const editMessages = editwidgetJQ.find(".editmsgs")
  const editContentDOM = editContent.get(0)
  const saveUrl = editContent.attr("saveurl")
  const readonlyContent = editwidgetJQ.find(".readonlycontent")

  const saveData = () => {
    const saveValue = JSON.stringify(editContent.val())
    console.warn(`save ${saveValue} to ${saveUrl}`)

    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: saveUrl,
      data: saveValue,
      processData: false,
      contentType: true,
      success: processSavedOK(saveValue),
      error: processSavedError,
    })
  }

  const processSavedOK = saveValue => response => {
    const { stat, messages, readonly } = response
    if (stat) {
      finishSave(saveValue, readonly)
    } else {
      abortSave(messages)
    }
  }

  const processSavedError = (jqXHR, stat) => {
    console.warn({ saveUrl })
    const { status, statusText } = jqXHR
    abortSave([[stat, `save failed: ${status} ${statusText}`]])
  }

  const finishSave = (saveValue, readonly) => {
    editContent.attr("origvalue", saveValue)
    readonlyContent.html(readonly)
    cancelButton.hide()
    returnButton.show()
    resetButton.hide()
    saveButton.hide()
  }

  const abortSave = messages => {
    editMessages.show()
    editMessages.html("")
    for (const message of messages) {
      const [tp, msg] = message
      const html = `<span class="msgitem ${tp}">${msg}</span>`
      editMessages.append(html)
    }
    cancelButton.show()
    returnButton.hide()
    resetButton.show()
    saveButton.show()
  }

  updateButton.off("click").click(() => {
    editContent.show()
    editContent.val(JSON.parse(editContent.attr("origvalue")))
    editContentDOM.addEventListener(
      "keyup",
      handleTyping({ cancelButton, returnButton, resetButton, saveButton }, editContent)
    )
    readonlyContent.hide()
    updateButton.hide()
    cancelButton.hide()
    returnButton.show()
    resetButton.hide()
    saveButton.hide()
    editMessages.hide()
  })
  cancelButton.off("click").click(() => {
    editContent.val("")
    editContent.hide()
    readonlyContent.show()
    updateButton.show()
    cancelButton.hide()
    returnButton.hide()
    resetButton.hide()
    saveButton.hide()
    editMessages.hide()
  })
  returnButton.off("click").click(() => {
    editContent.val("")
    editContent.hide()
    readonlyContent.show()
    updateButton.show()
    cancelButton.hide()
    returnButton.hide()
    resetButton.hide()
    saveButton.hide()
    editMessages.hide()
  })
  resetButton.off("click").click(() => {
    editContent.val(JSON.parse(editContent.attr("origvalue")))
    cancelButton.hide()
    returnButton.show()
    resetButton.hide()
    saveButton.hide()
    editMessages.hide()
  })
  saveButton.off("click").click(() => {
    saveData()
  })
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
  editWidgets()
})
