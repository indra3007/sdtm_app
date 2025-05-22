window.dash_clientside = Object.assign({}, window.dash_clientside, {
    spinner: {
        toggle: function(isLoading) {
            // if loading, show the custom spinner, else hide it.
            return isLoading ? {"display": "block"} : {"display": "none"};
        }
    }
});