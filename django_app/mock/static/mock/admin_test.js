document.addEventListener("DOMContentLoaded", function () {
  var section = document.getElementById("id_section");
  var duration = document.getElementById("id_duration_minutes");
  if (!section || !duration) return;

  section.addEventListener("change", function () {
    if (section.value === "reading") duration.value = "25";
    if (section.value === "listening") duration.value = "25";
    if (section.value === "quiz") duration.value = "25";
  });
});
