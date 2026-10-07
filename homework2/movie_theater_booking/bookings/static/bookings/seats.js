// Progressive enhancement: the form still books correctly without JavaScript.
const selectedSeat = document.querySelector("#selected-seat");
const seats = document.querySelectorAll(".seat-radio");
function updateSeat() {
  const selected = document.querySelector(".seat-radio:checked");
  selectedSeat.textContent = selected ? selected.dataset.number : "Choose a seat";
}
seats.forEach((seat) => seat.addEventListener("change", updateSeat));
updateSeat();
