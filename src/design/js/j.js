console.log("js file")

function findInList(stringToFind, idOfResultList) {
  let txtValue

  const elements2Filter = document.querySelectorAll(`#${idOfResultList}> *`)

  // Loop through all list items, and hide those who don't match the search query

  for (let i = 0; i < elements2Filter.length; i++) {
    let showItems = false
    const inner = elements2Filter[i].getElementsByClassName("tag")

    for (let j = 0; j < inner.length; j++) {
      txtValue = inner[j].innerHTML

      if (txtValue.toUpperCase().indexOf(stringToFind.toUpperCase()) > -1) {
        showItems = true
      }
    }

    // hide items if found
    if (showItems) {
      elements2Filter[i].style.display = ""
    } else {
      elements2Filter[i].style.display = "none"
    }
  }
}

function clearList(idOfResultList) {
  const elements2Filter = document.querySelectorAll(`#${idOfResultList}> *`)
  for (let i = 0; i < elements2Filter.length; i++) {
    elements2Filter[i].style.display = ""
  }
}

const createTageButtons = idOfResultList => {
  const tagNames = []

  // find all the tags items
  const elements2Filter = document.getElementsByClassName("tag")

  for (let i = 0; i < elements2Filter.length; i++) {
    tagNames.push(elements2Filter[i].innerHTML)
  }

  // get unique list of tags
  const uniqueTags = [...new Set(tagNames)]
  uniqueTags.sort()

  // create buttons
  if (uniqueTags.length > 0) {
    let output = "Filter op <br>"
    for (const item of uniqueTags) {
      output += `
        <button
          class="mButtonClean"
          onclick="findInList('${item}', '${idOfResultList}')">
            ${item}
        </button>
        <br>
      `
    }
    output += `
      <br>
      <button
        type="button"
        name="button"
        onclick="clearList('${idOfResultList}')">
          All results
      </button>`
    document.getElementById("filteronList").innerHTML = output
  }
}

createTageButtons("list1")

// Bind function to onclick event for checkbox
document.getElementById("langSwitch").onchange = function() {
  // access properties using this keyword
  if (this.checked) {
    window.location.href = "/en"
  } else {
    window.location.href = "/"
  }
}
