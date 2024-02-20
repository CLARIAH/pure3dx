// Add this code to your page

// <script src="js/headers-to-nav.js"></script>
// <script>
//   generateNavigationFromHeaders('h2', 'text-neutral-800')
// </script>

function generateNavigationFromHeaders(elementsToGet, classes) {
  let elementList = document.querySelectorAll(elementsToGet)

  let navListHTML = ""

  for (const elem of elementList) {
    const hId = saveName(elem.innerHTML)
    // add id to element
    elem.setAttribute("id", hId)

    // generate link
    navListHTML = `${navListHTML}<a href="#${hId}" class="${classes}">${elem.innerHTML}</a>`
  }

  document.getElementById("headerNavigation").innerHTML = navListHTML
}

const saveName = str => str.replaceAll(" ", "-").replaceAll("&", "").toLowerCase()
