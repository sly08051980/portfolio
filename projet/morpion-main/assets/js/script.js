console.log("hello");

let joueur = 0; 
let coupJouer = [];
let verifierCaseTouteCocher = ["a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "c3"];
let active = true;

document.querySelector('tbody').addEventListener('click', function(event) {
    if (active === true) {
        let cellule = event.target;
        let recupererCellule = cellule.id;

        
        if (!coupJouer.includes(recupererCellule)) {
            coupJouer.push(recupererCellule);
            console.log("Coup joué :", coupJouer);
        }

       
        if (joueur === 0 && cellule.innerHTML !== "X" && cellule.innerHTML !== "O") {
            cellule.innerHTML = "X";
            cellule.style.color = "white";
            console.log("Humain joue :", cellule.innerHTML);
            joueur = 1; 
            verifierGagnerligne();

            if (active) {
                setTimeout(botJoue, 500);
            }
        }
    }
});

function botJoue() {
    if (!active) return;

    let maTable = document.querySelector('tbody');
    let emptyCells = [];

    for (let i = 0; i < maTable.rows.length; i++) {
        for (let j = 0; j < maTable.rows[i].cells.length; j++) {
            let cell = maTable.rows[i].cells[j];
            if (cell.innerHTML !== "X" && cell.innerHTML !== "O") {
                emptyCells.push(cell.id);
            }
        }
    }
    if (emptyCells.length === 0) return; 

   
    let randomIndex = Math.floor(Math.random() * emptyCells.length);
    let chosenCellId = emptyCells[randomIndex];
    let chosenCell = document.getElementById(chosenCellId);
    chosenCell.innerHTML = "O";
    chosenCell.style.color = "red"; 
    console.log("Bot joue :", chosenCell.innerHTML, "sur", chosenCellId);
    joueur = 0; 
    coupJouer.push(chosenCellId);
    verifierGagnerligne();
}

function verifierGagnerligne() {
    let maTable = document.querySelector('tbody');
    
    for (let index = 0; index < 3; index++) {
        if (
            maTable.rows[index].cells[0].innerHTML === "O" &&
            maTable.rows[index].cells[1].innerHTML === "O" &&
            maTable.rows[index].cells[2].innerHTML === "O"
        ) {
            maTable.rows[index].cells[0].style.backgroundColor = "green";
            maTable.rows[index].cells[1].style.backgroundColor = "green";
            maTable.rows[index].cells[2].style.backgroundColor = "green";
            active = false;
            console.log("Bot gagne sur une ligne !");
            return;
        } else if (
            maTable.rows[index].cells[0].innerHTML === "X" &&
            maTable.rows[index].cells[1].innerHTML === "X" &&
            maTable.rows[index].cells[2].innerHTML === "X"
        ) {
            maTable.rows[index].cells[0].style.backgroundColor = "green";
            maTable.rows[index].cells[1].style.backgroundColor = "green";
            maTable.rows[index].cells[2].style.backgroundColor = "green";
            active = false;
            console.log("Humain gagne sur une ligne !");
            return;
        }
    }

    for (let index = 0; index < 3; index++) {
        if (
            maTable.rows[0].cells[index].innerHTML === "O" &&
            maTable.rows[1].cells[index].innerHTML === "O" &&
            maTable.rows[2].cells[index].innerHTML === "O"
        ) {
            maTable.rows[0].cells[index].style.backgroundColor = "green";
            maTable.rows[1].cells[index].style.backgroundColor = "green";
            maTable.rows[2].cells[index].style.backgroundColor = "green";
            active = false;
            console.log("Bot gagne sur une colonne !");
            return;
        } else if (
            maTable.rows[0].cells[index].innerHTML === "X" &&
            maTable.rows[1].cells[index].innerHTML === "X" &&
            maTable.rows[2].cells[index].innerHTML === "X"
        ) {
            maTable.rows[0].cells[index].style.backgroundColor = "green";
            maTable.rows[1].cells[index].style.backgroundColor = "green";
            maTable.rows[2].cells[index].style.backgroundColor = "green";
            active = false;
            console.log("Humain gagne sur une colonne !");
            return;
        }
    }
   
    if (
        maTable.rows[0].cells[0].innerHTML === "O" &&
        maTable.rows[1].cells[1].innerHTML === "O" &&
        maTable.rows[2].cells[2].innerHTML === "O"
    ) {
        maTable.rows[0].cells[0].style.backgroundColor = "green";
        maTable.rows[1].cells[1].style.backgroundColor = "green";
        maTable.rows[2].cells[2].style.backgroundColor = "green";
        active = false;
        console.log("Bot gagne sur la diagonale principale !");
        return;
    } else if (
        maTable.rows[0].cells[0].innerHTML === "X" &&
        maTable.rows[1].cells[1].innerHTML === "X" &&
        maTable.rows[2].cells[2].innerHTML === "X"
    ) {
        maTable.rows[0].cells[0].style.backgroundColor = "green";
        maTable.rows[1].cells[1].style.backgroundColor = "green";
        maTable.rows[2].cells[2].style.backgroundColor = "green";
        active = false;
        console.log("Humain gagne sur la diagonale principale !");
        return;
    } else if (
        maTable.rows[0].cells[2].innerHTML === "O" &&
        maTable.rows[1].cells[1].innerHTML === "O" &&
        maTable.rows[2].cells[0].innerHTML === "O"
    ) {
        maTable.rows[0].cells[2].style.backgroundColor = "green";
        maTable.rows[1].cells[1].style.backgroundColor = "green";
        maTable.rows[2].cells[0].style.backgroundColor = "green";
        active = false;
        console.log("Bot gagne sur la diagonale secondaire !");
        return;
    } else if (
        maTable.rows[0].cells[2].innerHTML === "X" &&
        maTable.rows[1].cells[1].innerHTML === "X" &&
        maTable.rows[2].cells[0].innerHTML === "X"
    ) {
        maTable.rows[0].cells[2].style.backgroundColor = "green";
        maTable.rows[1].cells[1].style.backgroundColor = "green";
        maTable.rows[2].cells[0].style.backgroundColor = "green";
        active = false;
        console.log("Humain gagne sur la diagonale secondaire !");
        return;
    }
    
   
    if (coupJouer.length === verifierCaseTouteCocher.length) {
        console.log("Match nul !");
        active = false;
    }
}

const boutonRejouer = document.querySelector('.boutton button');
boutonRejouer.addEventListener('click', rejouer);

function rejouer() {
  location.reload();
}
