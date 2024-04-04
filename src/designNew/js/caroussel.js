export class Caroussel {
  init(data, containerId) {
    this.containerId = containerId
    this.data = data
    this.curP = 0
  }

  nextI(i, step) {
    return (i + step) % this.data.length
  }

  adaptContainer() {
    document.getElementById(this.containerId).innerHTML = this.data.map((data, i) => `
        <div
          href="${data.projectLink}"
          class="absolute mx-auto left-0 right-0 bg-white transition-all z-0 bg-white" 
          id="pc${i}"
          style="width:300px; z-index:0"
        >
          <img
            src="images/${data.projectImg}"
            class="w-full"
            alt=""
            loading="lazy"
            id="pimg${i}"
          >
        </div>
    `
    ).join("\n")
  }

  rotateItems(direction) {
    this.curP = this.nextI(this.curP, direction, this.data)
    const curPpp = this.nextI(this.curP, -2, this.data)
    const curPp = this.nextI(this.curP, -1, this.data)
    const curPn = this.nextI(this.curP, 1, this.data)
    const curPnn = this.nextI(this.curP, 2, this.data)

    for (const { c, zIndex, width, transform, opacity, filter } of [
      {
        c: curPpp,
        zIndex: "30",
        width: "325px",
        transform: "translateX(-250px)",
        opacity: "0.5",
        filter: "blur(4px)",
      },
      {
        c: curPp,
        zIndex: "40",
        width: "350px",
        transform: "translateX(-150px)",
        opacity: "0.7",
        filter: "blur(2px)",
      },
      {
        c: this.curP,
        zIndex: "50",
        width: "400px",
        transform: "translateX(0px)",
        opacity: "1",
        filter: "blur(0px)",
      },
      {
        c: curPn,
        zIndex: "40",
        width: "350px",
        transform: "translateX(150px)",
        opacity: "0.7",
        filter: "blur(2px)",
      },
      {
        c: curPnn,
        zIndex: "30",
        width: "325px",
        transform: "translateX(250px)",
        opacity: "0.5",
        filter: "blur(4px)",
      },
    ]) {
      const pc = document.getElementById(`pc${c}`)
      const pimg = document.getElementById(`pimg${c}`)
      pc.style.zIndex = zIndex
      pc.style.width = width
      pc.style.transform = transform
      pc.style.filter = filter
      pimg.style.opacity = opacity
    }

    document.getElementById("sumTitle").innerHTML = this.data[this.curP].name
    document.getElementById("sumDescription").innerHTML = this.data[this.curP].description
    document.getElementById("sumImg").src = `images/${this.data[this.curP].projectImg}`
    document.getElementById("sumlink").href = this.data[this.curP].fileName
  }
  roll() {
    this.adaptContainer()
    this.rotateItems(0)
  }
}

//rotateItems(0)
