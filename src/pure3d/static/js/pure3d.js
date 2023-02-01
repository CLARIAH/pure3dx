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

const editRoles = () => {
  const editroles = $(".editroles")
  const assignButtons = $(`a.button[kind="edit_assign"]`)
  const topContent = $(".myadmin")

  editroles.each((i, editrole) => {
    editRole(editrole, assignButtons, topContent)
  })
}

const equalSets = (a, b) => a.size === b.size && [...a].every(value => b.has(value))

const editRole = (editrole, assignButtons, topContent) => {
  const editroleJQ = $(editrole)
  const assignButton = editroleJQ.find(`a.button[kind="edit_assign"]`)
  const cancelButton = editroleJQ.find(`a.button[kind="edit_cancel"]`)
  const saveButton = editroleJQ.find(`a.button[kind="edit_save"]`)
  const editContent = editroleJQ.find(".edit.roles")
  const eRoles = editContent.find(".role")
  const editMessages = editroleJQ.find(".editmsgs")
  const saveUrl = editContent.attr("saveurl")
  const multiple = editContent.attr("multiple")
  const origValue = new Set(editContent.attr("origvalue").split(","))
  const currentValue = new Set(editContent.attr("origvalue").split(","))

  editContent.hide()
  cancelButton.hide()
  saveButton.hide()

  const saveData = () => {
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: saveUrl,
      data: JSON.stringify(Array.from(currentValue)),
      processData: false,
      contentType: true,
      success: processSavedOK,
      error: processSavedError,
    })
  }

  const processSavedOK = response => {
    const { stat, messages, updated } = response
    if (stat) {
      finishSave(updated)
    } else {
      abortSave(messages)
    }
  }

  const processSavedError = (jqXHR, stat) => {
    const { status, statusText } = jqXHR
    abortSave([[stat, `save failed: ${status} ${statusText}`]])
  }

  const finishSave = updated => {
    topContent.html(updated)
    editRoles()
  }

  const abortSave = messages => {
    editMessages.html("")
    for (const message of messages) {
      const [tp, msg] = message
      const html = `<span class="msgitem ${tp}">${msg}</span>`
      editMessages.append(html)
    }
    editMessages.show()

    cancelButton.show()
    saveButton.show()
  }

  const handleClicking = e => {
    const elem = $(e.target)
    const role = elem.attr("role")
    if (multiple) {
      if (elem.hasClass("on")) {
        elem.removeClass("on")
        currentValue.delete(role)
      } else {
        elem.addClass("on")
        currentValue.add(role)
      }
    } else {
      eRoles.each((j, eRole) => {
        const eRoleJQ = $(eRole)
        const eStr = eRoleJQ.attr("role")
        if (eStr == role) {
          eRoleJQ.addClass("on")
          currentValue.add(eStr)
        } else {
          eRoleJQ.removeClass("on")
          currentValue.delete(eStr)
        }
      })
    }
    if (equalSets(origValue, currentValue)) {
      editContent.removeClass("dirty")
      cancelButton.hide()
      saveButton.show()
    } else {
      editContent.addClass("dirty")
      cancelButton.show()
      saveButton.show()
    }
  }

  assignButton.off("click").click(() => {
    editroleJQ.addClass("editing")
    editContent.val(editContent.attr("origvalue"))
    editContent.removeClass("dirty")
    eRoles.off("click").click(handleClicking)
    editContent.show()
    editMessages.html("")
    editMessages.hide()

    assignButtons.hide()
    cancelButton.hide()
    saveButton.show()
  })
  cancelButton.off("click").click(() => {
    editContent.val(editContent.attr("origvalue"))
    editContent.removeClass("dirty")
    editMessages.html("")
    editMessages.hide()

    cancelButton.hide()
    saveButton.show()
  })
  saveButton.off("click").click(() => {
    if (equalSets(origValue, currentValue)) {
      editroleJQ.removeClass("editing")
      editContent.removeClass("dirty")
      editContent.hide()
      editMessages.html("")
      editMessages.hide()

      assignButtons.show()
      cancelButton.hide()
      saveButton.hide()
    } else {
      saveData()
    }
  })
}

const editWidgets = () => {
  const editwidgets = $(".editwidget")

  editwidgets.each((i, editwidget) => {
    editWidget(editwidget)
  })
}

const editWidget = editwidget => {
  const editwidgetJQ = $(editwidget)
  const updateButton = editwidgetJQ.find(`a.button[kind="edit_update"]`)
  const cancelButton = editwidgetJQ.find(`a.button[kind="edit_cancel"]`)
  const saveButton = editwidgetJQ.find(`a.button[kind="edit_save"]`)
  const editContent = editwidgetJQ.find(".editcontent")
  const editMessages = editwidgetJQ.find(".editmsgs")
  const saveUrl = editContent.attr("saveurl")
  const readonlyContent = editwidgetJQ.find(".readonlycontent")

  editContent.hide()
  cancelButton.hide()
  saveButton.hide()

  const saveData = saveValue => {
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: saveUrl,
      data: JSON.stringify(saveValue),
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
    const { status, statusText } = jqXHR
    abortSave([[stat, `save failed: ${status} ${statusText}`]])
  }

  const finishSave = (saveValue, readonly) => {
    editwidgetJQ.removeClass("editing")
    readonlyContent.html(readonly)
    readonlyContent.show()
    editContent.val("")
    editContent.attr("origvalue", saveValue)
    editContent.removeClass("dirty")
    editContent.hide()
    editMessages.hide()

    updateButton.show()
    cancelButton.hide()
    saveButton.hide()
  }

  const abortSave = messages => {
    editMessages.html("")
    for (const message of messages) {
      const [tp, msg] = message
      const html = `<span class="msgitem ${tp}">${msg}</span>`
      editMessages.append(html)
    }
    editMessages.show()

    cancelButton.show()
    saveButton.show()
  }

  const handleTyping = () => {
    const value = editContent.val()
    const origValue = editContent.attr("origvalue")
    if (origValue == value) {
      editContent.removeClass("dirty")
      cancelButton.hide()
      saveButton.show()
    } else {
      editContent.addClass("dirty")
      cancelButton.show()
      saveButton.show()
    }
  }

  updateButton.off("click").click(() => {
    editwidgetJQ.addClass("editing")
    readonlyContent.hide()
    editContent.val(editContent.attr("origvalue"))
    editContent.removeClass("dirty")
    editContent.off("keyup").keyup(handleTyping)
    editContent.show()
    editMessages.html("")
    editMessages.hide()

    updateButton.hide()
    cancelButton.hide()
    saveButton.show()
  })
  cancelButton.off("click").click(() => {
    editContent.val(editContent.attr("origvalue"))
    editContent.removeClass("dirty")
    editMessages.html("")
    editMessages.hide()

    cancelButton.hide()
    saveButton.show()
  })
  saveButton.off("click").click(() => {
    const origValue = editContent.attr("origvalue")
    const saveValue = editContent.val()
    if (origValue == saveValue) {
      editwidgetJQ.removeClass("editing")
      readonlyContent.show()
      editContent.val("")
      editContent.removeClass("dirty")
      editContent.hide()
      editMessages.html("")
      editMessages.hide()

      updateButton.show()
      cancelButton.hide()
      saveButton.hide()
    } else {
      saveData(saveValue)
    }
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
  editRoles()
})
