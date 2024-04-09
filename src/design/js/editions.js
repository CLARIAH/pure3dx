console.log('yo');

function showSum(id) {
    let elementList = document.querySelectorAll('.editSum')

    elementList.forEach(elem => {
        elem.classList.remove("flex");
        elem.classList.add("hidden");
    });

    document.getElementById(id).classList.add("flex");
}

