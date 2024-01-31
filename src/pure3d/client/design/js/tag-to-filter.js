/*
HTML structure:
<ul id="filterList">
  <li>
    <div data-tag-to-facet="{facetName}">
      <span>item1</span> <span>item2</span>
    </div>
  </li>
</ul>

<div id="facetsList"></div>

-------------------------------------------
*/

const facets = [] // facet json
const selectedFacets = [] // facet json
const results = [] // facet json

//get Raw html
const allContainerElems = document.querySelectorAll("[data-tag-to-facet]")

const allFacetsNames = []

allContainerElems.forEach(listItem => {
  const att = listItem.getAttribute("data-tag-to-facet")
  allFacetsNames.push(att)
})

uniqueArr(allFacetsNames).forEach(fName => {
  facets.push({
    facetName: fName,
    faceItemsRaw: [],
    faceItems: [],
  })

  selectedFacets.push({
    facetName: fName,
  })
})

//console.log(allContainerElems);
facets.forEach(facetItem => {
  allContainerElems.forEach(containerItem => {
    if (facetItem.facetName == containerItem.getAttribute("data-tag-to-facet")) {
      for (const item of containerItem.getElementsByTagName("span")) {
        //console.log(item.innerHTML);
        facetItem.faceItemsRaw.push(item.innerHTML)
      }
    }
  })

  facetItem.faceItems = uniqueArr(facetItem.faceItemsRaw).sort()
  delete facetItem.faceItemsRaw
})

// generate facets
let facetsHTML = ""

for (const facet of facets) {
  facetsHTML += `
    <div class="">
      <strong>${facet.facetName}</strong>
      <div class="flex flex-col">
  `
  for (const [index, fItem] of facet.facetItems.entries()) {
    facetsHTML += `
      <div class="text-sm">
        <input
          type="checkbox"
          id="${facet.facetName}${index}"
          name="${facet.facetName}${index}"
          value="${fItem}"
          class="mr-1"
          onChange="handleFacetedSearch()"
          data-facetName="${facet.facetName}"
        >
        <label for="${facet.facetName}${index}">${fItem}</label>
      </div>
    `
  }

  facetsHTML += "</div>"
  facetsHTML += "</div>"
}

document.getElementById("facetsList").innerHTML = facetsHTML

// get results
const allresults = document.getElementById("filterList").children

for (const result of allresults) {
  if (result.id !== "surprise") {
    const rItem = {}
    rItem.id = result.id
    rItem.meta = []

    facets.forEach(facet => {
      rItem.meta[facet.facetName] = []

      const metadata1 = result.querySelector(`[data-tag-to-facet="${facet.facetName}"]`)
      for (const metadataItem of metadata1.children) {
        rItem.meta[facet.facetName].push(metadataItem.innerHTML)
      }
    })

    results.push(rItem)
  }
}

function handleFacetedSearch() {
  const allCheckboxes = document.querySelectorAll("[data-facetName]")
  let leastOne = false
  allCheckboxes.forEach(cBoxItem => {
    if (cBoxItem.checked) {
      leastOne = true
    }
  })
  console.log(leastOne)

  // get all results
  const allresults = document.getElementById("filterList").children
  for (const result of allresults) {
    if (leastOne) {
      let showItem = false
      result.classList.remove("flex")
      result.classList.add("hidden")

      results.forEach(resultItem => {
        if (result.id == resultItem.id) {
          const allCheckboxes = document.querySelectorAll("[data-facetName]")
          allCheckboxes.forEach(cBoxItem => {
            if (cBoxItem.checked) {
              if (
                resultItem.meta[cBoxItem.getAttribute("data-facetName")].includes(
                  cBoxItem.value
                )
              ) {
                showItem = true
              }
            }
          })
        }
      })

      if (showItem) {
        console.log(result)
        result.classList.add("flex")
        result.classList.remove("hidden")
      }
    } else {
      result.classList.add("flex")
      result.classList.remove("hidden")
    }
  }
}

function uniqueArr(a) {
  return a
    .sort()
    .filter((value, index, array) => index === 0 || value !== array[index - 1])
}

function handleClass(id, action, className) {
  if (action == "add") {
    document.getElementById(id).classList.add(className)
  } else if (action == "remove") {
    document.getElementById(id).classList.remove(className)
  }
}
