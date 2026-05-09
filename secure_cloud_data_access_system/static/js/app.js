const selectedImages = [];
const imageInput = document.getElementById("image_pattern");
const counter = document.getElementById("image-sequence-display");

function syncImageSequence() {
  if (imageInput) {
    imageInput.value = selectedImages.join(",");
  }
  if (counter) {
    counter.textContent = `${selectedImages.length} selected`;
  }
  document.querySelectorAll(".image-card").forEach((card) => {
    const image = card.dataset.image;
    const badge = card.querySelector(".image-badge");
    const index = selectedImages.indexOf(image);
    if (index >= 0) {
      card.classList.add("selected");
      badge.textContent = index + 1;
    } else {
      card.classList.remove("selected");
      badge.textContent = "";
    }
  });
}

document.querySelectorAll(".image-card").forEach((card) => {
  card.addEventListener("click", () => {
    const image = card.dataset.image;
    const index = selectedImages.indexOf(image);
    if (index >= 0) {
      selectedImages.splice(index, 1);
    } else {
      if (selectedImages.length >= 5) return;
      selectedImages.push(image);
    }
    syncImageSequence();
  });
});

document.querySelectorAll("[data-reset-images='true']").forEach((button) => {
  button.addEventListener("click", () => {
    selectedImages.length = 0;
    syncImageSequence();
  });
});

syncImageSequence();
