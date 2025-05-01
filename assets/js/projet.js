document.addEventListener("DOMContentLoaded", () => {
    let allProjects = []; 
    const choix = document.getElementById('choix');
    const container = document.getElementById('card-container');
    const countDisplay = document.querySelector('.nombre');
    let count = 0;
  
    const tagsDisponibles = ["Tous", "Symfony", "JavaScript", "NodeJs", "Python", "Java", "PayPal", "Bootstrap"];
  
    tagsDisponibles.forEach((item) => {
      const button = document.createElement('button');
      button.textContent = item;
  
      button.className = item === "Tous"
        ? 'btn btn-violet m-2 rounded-pill fs-14'
        : 'btn btn-light m-2 rounded-pill fs-14';
  
      button.addEventListener('click', () => {
        
        choix.querySelectorAll('button').forEach(btn => {
          btn.classList.remove('btn-violet');
          btn.classList.add('btn-light');
        });
        button.classList.remove('btn-light');
        button.classList.add('btn-violet');
  
      
        const tagChoisi = item;
        const projetsFiltres = tagChoisi === "Tous"
          ? allProjects
          : allProjects.filter(p => p.tags.includes(tagChoisi));
  
        afficherCartes(projetsFiltres);
      });
  
      choix.appendChild(button);
    });
  
    
    fetch('assets/json/listProjet.json')
      .then(response => response.json())
      .then(data => {
        allProjects = data;
        afficherCartes(allProjects); 
      });

    function afficherCartes(projets) {
      container.innerHTML = "";
      count = 0;
  
      projets.forEach(item => {
        const col = document.createElement('div');
        col.className = 'col-12 col-md-6 col-lg-4 mb-4';
  
        const tagsHTML = item.tags.map(tag => `<p class="arrondie rounded-pill mb-0">${tag}</p>`).join('');
        const texteCacheHTML = item.texteCache.map(line => `<li>${line}</li>`).join('');
        const telechargerBouton = item.telecharger
        ? `<a href="${item.telecharger}" class="btn arrondie fs-14 font-500" target="_blank" rel="noopener noreferrer">Télécharger</a>`
        : "";
        col.innerHTML = `
        <div class="card p-3 h-100 shadow p-5 zoom">
          <h5 class="card-titre fs-24 violet lineh-24"><strong>${item.titre}</strong></h5>
          <p class="card-text fs-14 font-400 lineh-20">${item.text}</p>
          <div class="card-body"><p>${item.contenu}</p></div>
          <div class="row">
            <div class="col-12 d-flex gap-2 flex-wrap mt-3 fs-12 font-600">${tagsHTML}</div>
          </div>
          <div class="afficher mt-2" style="display: none;">
            <strong class="fs-14 font-500">Fonctionnalités :</strong>
            <ul class="font-400 fs-14 gris">${texteCacheHTML}</ul>
          </div>
          <div class="d-flex justify-content-between mt-2 flex-wrap gap-2">
            <button type="button" class="btn btn-violet btn-voir fs-14 font-500">Voir plus</button>
            ${telechargerBouton}
            <a href="${item.lien}" class="btn arrondie fs-14 font-500" target="_blank" rel="noopener noreferrer">Visiter</a>
          </div>
        </div>
      `;
  
        container.appendChild(col);
        count++;
      });
  
      countDisplay.textContent = `Projets : ${count}`;
    }
  
   
    document.addEventListener("click", function (e) {
      if (e.target.classList.contains("btn-voir")) {
        const card = e.target.closest(".card");
        const afficher = card.querySelector(".afficher");
        if (afficher.style.display === "none") {
          afficher.style.display = "block";
          e.target.textContent = "Voir moins";
        } else {
          afficher.style.display = "none";
          e.target.textContent = "Voir plus";
        }
      }
    });
    window.addEventListener("scroll", () => {
        const navbar = document.getElementById("main-navbar");
        if (window.scrollY > 10) {
          navbar.classList.remove("bg-transparent");
          navbar.classList.add("bg-white", "shadow"); 
        } else {
          navbar.classList.add("bg-transparent");
          navbar.classList.remove("bg-white", "shadow");
        }
      });
  });
  