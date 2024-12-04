export class Carousel {
  constructor(data, containerId, backId, nextId) {
    this.containerId = containerId
    this.backId = backId
    this.nextId = nextId
    this.data = data
    this.curP = 0
  }

  nextI(i, step) {
    const result = (i + step + this.data.length) % this.data.length
    return result
  }

  rotateItems(direction) {
    this.curP = this.nextI(this.curP, direction, this.data)
    const curPpp = this.nextI(this.curP, -2, this.data)
    const curPp = this.nextI(this.curP, -1, this.data)
    const curPn = this.nextI(this.curP, 1, this.data)
    const curPnn = this.nextI(this.curP, 2, this.data)

    for (const { c, zIndex, height, transform, opacity, filter } of [
      {
        c: curPpp,
        zIndex: "30",
        height: "150px",
        transform: "translateX(-250px)",
        opacity: "0.5",
        filter: "blur(4px)",
      },
      {
        c: curPp,
        zIndex: "40",
        height: "175px",
        transform: "translateX(-150px)",
        opacity: "0.7",
        filter: "blur(2px)",
      },
      {
        c: this.curP,
        zIndex: "50",
        height: "200px",
        transform: "translateX(0px)",
        opacity: "1",
        filter: "blur(0px)",
      },
      {
        c: curPn,
        zIndex: "40",
        height: "175px",
        transform: "translateX(150px)",
        opacity: "0.7",
        filter: "blur(2px)",
      },
      {
        c: curPnn,
        zIndex: "30",
        height: "150px",
        transform: "translateX(250px)",
        opacity: "0.5",
        filter: "blur(4px)",
      },
    ]) {
      const pc = document.getElementById(`pc${c}`)
      const pimg = document.getElementById(`pimg${c}`)
      pc.style.zIndex = zIndex
      pimg.style.height = height
      pc.style.transform = transform
      pc.style.filter = filter
      pimg.style.opacity = opacity
    }

    document.getElementById("sumTitle").innerHTML = this.data[this.curP].name
    document.getElementById("sumCreator").innerHTML = this.data[this.curP].creator
    document.getElementById("sumAbstract").innerHTML = this.data[this.curP].abstract
    document.getElementById("sumImg").src = `/project/${
      this.data[this.curP].num
    }/icon.png`
    document.getElementById("sumlink1").href = this.data[this.curP].fileName
    document.getElementById("sumlink2").href = this.data[this.curP].fileName
  }
  init() {
    window.addEventListener("load", () => {
      for (const { rot, dr } of [
        { rot: this.backId, dr: -1 },
        { rot: this.nextId, dr: 1 },
      ]) {
        document
          .getElementById(rot)
          .addEventListener("click", () => this.rotateItems(dr))
      }

      document.getElementById(this.containerId).innerHTML = this.data
        .map(
          (p, i) => `
          <div
            href=""
            class="absolute mx-auto left-0 right-0 transition-all z-0 overflow-hidden h-56 bg-white" 
            id="pc${i}"
            style="width:300px; z-index:0"
            aria-label="Go to project: ${p.name}"
          >
            <img
              src="/project/${p.num}/icon.png"
              class="w-full border-2 border-white rounded shadow-lg"
              alt=""
              loading="lazy"
              id="pimg${i}"
            >
          </div>
      `
        )
        .join("\n")
      this.rotateItems(0)
    })
  }
}
