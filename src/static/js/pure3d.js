/*eslint-env jquery*/

const flashInit = () => {
  const msgbar = $("#messages")
  const dismiss = $("#flashdismiss")

  dismiss.off("click").click(() => {
    const msgs = msgbar.children("span")
    msgs.remove()
    dismiss.hide()
  })
  flashUpdate()
}

const flashUpdate = () => {
  const msgbar = $("#messages")
  const dismiss = $("#flashdismiss")
  const msgs = msgbar.children("span")
  if (msgs.length) {
    dismiss.show()
  } else {
    dismiss.hide()
  }
}

const addMsg = (tp, msg, replace = false) => {
  const msgbar = $("#messages")
  const dismiss = $("#flashdismiss")
  const msgs = msgbar.children("span")
  const html = `<span class="msgitem ${tp}">${msg}</span>`
  if (replace) {
    msgs.remove()
  }
  msgbar.append(html)
  dismiss.show()
}

const addMsgs = (messages, replace = false) => {
  const msgbar = $("#messages")
  const msgs = msgbar.children("span")
  if (replace) {
    msgs.remove()
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

const createUser = () => {
  const topContent = $(".myadmin")
  const userInfo = topContent.find("div.createuser")
  const button = userInfo.find("a")
  const userName = userInfo.find("input")
  const saveUrl = button.attr("href")
  button.off("click").click(() => {
    const name = userName
      .val()
      .trim()
      .replaceAll(" ", ".")
      .replaceAll(/[^A-Za-z0-9._-]/g, "_")
      .toLowerCase()
    button.attr("href", `${saveUrl}/${name}`)
    return true
  })
}

const editRoles = () => {
  const editroles = $(".editroles")
  const topContent = $(".myadmin")

  editroles.each((i, editrole) => {
    editRole(editrole, topContent)
  })
}

const editRole = (editrole, topContent) => {
  const editroleJQ = $(editrole)
  const assignButton = editroleJQ.find(`a.button[kind="edit_assign"]`)
  const cancelButton = editroleJQ.find(`a.button[kind="edit_cancel"]`)
  const saveButton = editroleJQ.find(`a.button[kind="edit_save"]`)
  const editContent = editroleJQ.find(".edit.roles")
  const eRoles = editContent.find(".role")
  const editMessages = editroleJQ.find(".editmsgs")
  const saveUrl = editContent.attr("saveurl")
  const origValue = editContent.attr("origvalue")
  let currentValue = origValue

  editContent.hide()
  cancelButton.hide()
  saveButton.hide()

  const saveData = () => {
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: saveUrl,
      data: JSON.stringify(currentValue),
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
    processMyWork()
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

  const setRole = role => {
    currentValue = origValue
    eRoles.each((i, eRole) => {
      const eRoleJQ = $(eRole)
      const eStr = eRoleJQ.attr("role") || null
      if (eStr == role) {
        if (!eRoleJQ.hasClass("on")) {
          eRoleJQ.addClass("on")
          currentValue = role
        }
      } else {
        if (eRoleJQ.hasClass("on")) {
          eRoleJQ.removeClass("on")
        }
      }
    })
  }

  const handleClicking = e => {
    const elem = $(e.target)
    const role = elem.attr("role") || null
    setRole(role)
    if (origValue == currentValue) {
      cancelButton.hide()
      saveButton.show()
    } else {
      cancelButton.show()
      saveButton.show()
    }
  }

  assignButton.off("click").click(() => {
    eRoles.off("click").click(handleClicking)
    setRole(origValue)
    editContent.show()
    editMessages.html("")
    editMessages.hide()

    modalizeButtons(false)
    cancelButton.hide()
    saveButton.show()
  })
  cancelButton.off("click").click(() => {
    setRole(editContent.attr("origvalue"))
    editMessages.html("")
    editMessages.hide()

    cancelButton.hide()
    saveButton.show()
  })
  saveButton.off("click").click(() => {
    if (origValue == currentValue) {
      editContent.hide()
      editMessages.html("")
      editMessages.hide()

      modalizeButtons(true)
      cancelButton.hide()
      saveButton.hide()
    } else {
      saveData()
    }
  })
}

const modalizeButtons = onOff => {
  const assignButtons = $(`a.button[kind="edit_assign"]`)
  const linkButtons = $(`a.button[kind="edit_link"]`)
  if (onOff) {
    assignButtons.show()
    linkButtons.show()
  } else {
    assignButtons.hide()
    linkButtons.hide()
  }
}

const linkUsers = () => {
  const linkusers = $(".linkusers")
  const topContent = $(".myadmin")

  linkusers.each((i, linkuser) => {
    linkUser(linkuser, topContent)
  })
}

const linkUser = (linkuser, topContent) => {
  const linkuserJQ = $(linkuser)
  const linkButton = linkuserJQ.find(`a.button[kind="edit_link"]`)
  const cancelButton = linkuserJQ.find(`a.button[kind="edit_cancel"]`)
  const saveButton = linkuserJQ.find(`a.button[kind="edit_save"]`)
  const roleContent = linkuserJQ.find(".chooseroles")
  const eRoles = roleContent.find(".role")
  const userContent = linkuserJQ.find(".chooseusers")
  const eUsers = userContent.find(".user")
  const editMessages = linkuserJQ.find(".editmsgs")
  const saveUrl = linkuserJQ.attr("saveurl")
  const origRole = null
  const initRole = eRoles.length == 1 ? eRoles.attr("role") : null
  let currentRole = initRole
  const origUser = null
  let currentUser = origUser

  roleContent.hide()
  userContent.hide()
  cancelButton.hide()
  saveButton.hide()

  const saveData = () => {
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: saveUrl,
      data: JSON.stringify([currentRole, currentUser]),
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
    processMyWork()
  }

  const abortSave = messages => {
    editMessages.html("")
    for (const [tp, msg] of messages) {
      const html = `<span class="msgitem ${tp}">${msg}</span>`
      editMessages.append(html)
    }
    editMessages.show()

    cancelButton.show()
    saveButton.show()
  }

  const setRole = role => {
    currentRole = origRole
    eRoles.each((i, eRole) => {
      const eRoleJQ = $(eRole)
      const eStr = eRoleJQ.attr("role") || null
      if (eStr == role) {
        if (!eRoleJQ.hasClass("on")) {
          eRoleJQ.addClass("on")
          currentRole = role
        }
      } else {
        if (eRoleJQ.hasClass("on")) {
          eRoleJQ.removeClass("on")
        }
      }
    })
  }

  const setUser = user => {
    currentUser = origUser
    eUsers.each((i, eUser) => {
      const eUserJQ = $(eUser)
      const eStr = eUserJQ.attr("user") || null
      if (eStr == user) {
        if (!eUserJQ.hasClass("on")) {
          eUserJQ.addClass("on")
          currentUser = user
        }
      } else {
        if (eUserJQ.hasClass("on")) {
          eUserJQ.removeClass("on")
        }
      }
    })
  }

  const handleClicking = e => {
    const elem = $(e.target)
    if (elem.hasClass("role")) {
      const role = elem.attr("role") || null
      setRole(role)
    } else {
      const user = elem.attr("user") || null
      setUser(user)
    }
    if (currentRole == origRole && currentUser == origUser) {
      cancelButton.hide()
      saveButton.show()
    } else {
      cancelButton.show()
      if (currentRole != origRole && currentUser != origUser) {
        saveButton.show()
      } else {
        saveButton.hide()
      }
    }
  }

  linkButton.off("click").click(() => {
    eRoles.off("click").click(handleClicking)
    eUsers.off("click").click(handleClicking)
    setRole(initRole)
    setUser(origUser)
    roleContent.show()
    userContent.show()
    editMessages.html("")
    editMessages.hide()

    modalizeButtons(false)
    if (currentRole == origRole && currentUser == origUser) {
      cancelButton.hide()
    } else {
      cancelButton.show()
    }
    saveButton.show()
  })
  cancelButton.off("click").click(() => {
    setRole(origRole)
    setUser(origUser)
    editMessages.html("")
    editMessages.hide()

    cancelButton.hide()
    saveButton.show()
  })
  saveButton.off("click").click(() => {
    if (currentRole == origRole && currentUser == origUser) {
      roleContent.hide()
      userContent.hide()
      editMessages.html("")
      editMessages.hide()

      modalizeButtons(true)
      cancelButton.hide()
      saveButton.hide()
    } else {
      saveData()
    }
  })
}

const kwmanageWidgets = () => {
  const kwmanagewidgets = $(".kwmanagewidget")
  const topContent = $(".myadmin")

  kwmanagewidgets.each((i, kwmanagewidget) => {
    kwmanageWidget(kwmanagewidget, topContent)
  })
}

const kwmanageWidget = (kwmanagewidget, topContent) => {
  const kwmanagewidgetJQ = $(kwmanagewidget)
  const cancelButton = kwmanagewidgetJQ.find(`a.button[kind="kwmanage_cancel"]`)
  const saveButton = kwmanagewidgetJQ.find(`a.button[kind="kwmanage_save"]`)
  const deleteButtons = kwmanagewidgetJQ.find(`span[delurl]`)
  const editContent = kwmanagewidgetJQ.find(".editcontent")
  const editMessages = kwmanagewidgetJQ.find(".editmsgs")
  const saveUrl = editContent.attr("saveurl")
  const name = editContent.attr("name")

  const saveData = saveValue => {
    const { name } = saveValue
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: saveUrl,
      data: JSON.stringify(saveValue),
      processData: false,
      contentType: true,
      success: processOK("save", name),
      error: processError("save", name),
    })
  }

  const delData = (delUrl, delValue) => {
    const { name } = delValue
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: delUrl,
      data: JSON.stringify(delValue),
      processData: false,
      contentType: true,
      success: processOK("delete", name),
      error: processError("delete", name),
    })
  }

  const processOK = (kind, name) => response => {
    const { stat, messages, updated } = response
    if (stat) {
      finishSave(name, updated)
    } else {
      abortSave(name, [[false, `${kind} failed`]] + messages)
    }
  }

  const processError = (kind, name) => (jqXHR, stat) => {
    const { status, statusText } = jqXHR
    abortSave(name, [[stat, `${kind} failed: ${status} ${statusText}`]])
  }

  const finishSave = (name, updated) => {
    console.warn({ name })
    topContent.html(updated)
    processMyWork(name)
  }

  const abortSave = (name, messages) => {
    $(`[itemkey="keywordlist-${name}"]`).prop("open", true)
    editMessages.html("")
    for (const [tp, msg] of messages) {
      const html = `<span class="msgitem ${tp}">${msg}</span>`
      editMessages.append(html)
    }
    editMessages.show()

    cancelButton.show()
    saveButton.show()
  }

  const handleTyping = () => {
    const value = editContent.val()
    if ("" == value) {
      editContent.removeClass("dirty")
      cancelButton.hide()
      saveButton.hide()
    } else {
      editContent.addClass("dirty")
      cancelButton.show()
      saveButton.show()
    }
  }

  cancelButton.off("click").click(() => {
    editContent.val("")
    editContent.removeClass("dirty")
    editMessages.html("")
    editMessages.hide()
    cancelButton.hide()
    saveButton.hide()
  })
  saveButton.off("click").click(() => {
    const saveValue = editContent.val()
    if ("" == saveValue) {
      editContent.val("")
      editContent.removeClass("dirty")
      editMessages.html("")
      editMessages.hide()
      cancelButton.hide()
      saveButton.hide()
    } else {
      saveData({ value: saveValue, name })
    }
  })
  deleteButtons.off("click").click(e => {
    const elem = $(e.target)
    const delUrl = elem.attr("delurl")
    delData(delUrl, { name: elem.attr("name"), value: elem.attr("value") })
  })

  editContent.removeClass("dirty")
  editContent.off("keyup").keyup(handleTyping)
  editMessages.html("")
  editMessages.hide()
  cancelButton.hide()
  saveButton.hide()
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
    for (const [tp, msg] of messages) {
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

  const accept = finput.attr("accept") || ""
  const acceptExtensions = new Set(accept.split(",").map(x => x.trim().slice(1)))
  acceptExtensions.delete("")

  fupdate.off("click").click(e => {
    e.preventDefault()
    e.stopPropagation()
    finput.click()
  })

  fdelete.off("click").click(e => {
    e.preventDefault()
    e.stopPropagation()
    const eJQ = $(e.currentTarget)
    const deleteUrl = eJQ.attr("url")
    fetchData(deleteUrl, "delete", fupload)
  })

  finput.change(() => {
    const theFile = finput.prop("files")[0]
    const theName = theFile.name
    const theExt = theName.split(".").slice(-1)[0] || ""
    if (!acceptExtensions.has(theExt)) {
      addMsg(
        "error",
        `The chosen file is ${theName}, but it's extension is not in the list ` +
          `of accepted extensions ${accept}. Choose an other file.`
      )
      return false
    }
    const xhr = new XMLHttpRequest()
    const { upload } = xhr

    const handleRequestEvent = () => {
      const { readyState, status, response } = xhr
      if (readyState === XMLHttpRequest.DONE) {
        if (status >= 200 && status < 400) {
          const { status: responseStatus, msgs, content } = response
          if (msgs) {
            for (const [typ, msg] of msgs) {
              addMsg(typ, msg, false)
            }
            if (responseStatus) {
              addMsg("good", "uploaded file saved on the server", false)
              fuploadJQ.html(content)
              uploadControl(fupload)
            } else {
              addMsg("error", "uploaded file not saved on the server", false)
            }
          }
          finput.val("")
        } else {
          addMsg("error", `Upload ended with status ${status}`, false)
        }
      } else {
        // pass
      }
    }
    const handleUploadEvent = e => {
      const { type, lengthComputable, loaded, total } = e
      const complete = lengthComputable ? Math.round((loaded / total) * 100) : "??"
      const msg = `uploading (${complete} %)`

      if (type == "loadstart") {
        addMsg("info", `${msg} ...`)
      } else if (type == "progress") {
        addMsg("info", `${msg} ...`)
      } else if (type == "load") {
        addMsg("info", `${msg} OK`)
      } else if (type == "error") {
        addMsg("info", `${msg} Failed`)
      } else if (type == "abort") {
        addMsg("info", `${msg} Aborted`)
      } else if (type == "timeout") {
        addMsg("info", `${msg} Timed out`)
      } else if (type == "loadend") {
        // pass
      } else {
        addMsg("warning", `upload ${type} (??)`)
      }
    }

    upload.addEventListener("loadstart", handleUploadEvent)
    upload.addEventListener("load", handleUploadEvent)
    upload.addEventListener("loadend", handleUploadEvent)
    upload.addEventListener("progress", handleUploadEvent)
    upload.addEventListener("error", handleUploadEvent)
    upload.addEventListener("abort", handleUploadEvent)
    upload.addEventListener("timeout", handleUploadEvent)
    xhr.addEventListener("readystatechange", handleRequestEvent)

    xhr.responseType = "json"
    xhr.open("POST", `${saveUrl}/${theFile.name}`)
    xhr.send(theFile)
  })
}

const confirmInit = () => {
  const confirmButtons = $(`a[confirm="v"]`)
  confirmButtons.each((i, confirmButton) => {
    const confirmButtonJQ = $(confirmButton)
    const lnk = confirmButtonJQ.attr("href")
    const tip = confirmButtonJQ.attr("title")
    confirmButtonJQ.off("click").click(e => {
      e.preventDefault()
      const confirmed = window.confirm(`Are you sure to ${tip}?`)
      if (confirmed) {
        window.location.href = lnk
      } else {
        // pass
      }
    })
  })
}

const processMyWork = name => {
  kwmanageWidgets()
  if (name) {
    $(`[itemkey="keywordlist-${name}"]`).prop("open", true)
  }
  editRoles()
  createUser()
  linkUsers()
  confirmInit()
}

$(() => {
  uploadControls()
  kwmanageWidgets()
  editWidgets()
  processMyWork()
  confirmInit()
  flashInit()
})
