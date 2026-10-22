// Os mesmos campos continuam sendo validados no servidor, com ou sem JavaScript.
const tipo = document.getElementById('tipo');
function atualizarCampos() {
    document.querySelectorAll('[data-tipos]').forEach((grupo) => {
        const ativo = grupo.dataset.tipos.split(' ').includes(tipo.value);
        grupo.hidden = !ativo;
        grupo.querySelectorAll('input').forEach((input) => {
            input.disabled = !ativo;
            input.required = ativo;
        });
    });
}
tipo.addEventListener('change', atualizarCampos);
atualizarCampos();
