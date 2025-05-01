
  document.addEventListener("DOMContentLoaded", function () {
    const banniere = document.getElementById("banniere-cookies");
    const accepter = document.getElementById("accepter-cookies");
    const refuser = document.getElementById("refuser-cookies");

    // Vérifie si l'utilisateur a déjà fait un choix
    if (!localStorage.getItem("cookies_consentement")) {
      banniere.classList.remove("d-none");
    }

    accepter.addEventListener("click", () => {
      localStorage.setItem("cookies_consentement", "accepte");
      banniere.classList.add("d-none");
    });

    refuser.addEventListener("click", () => {
      localStorage.setItem("cookies_consentement", "refuse");
      banniere.classList.add("d-none");
    });
  });

