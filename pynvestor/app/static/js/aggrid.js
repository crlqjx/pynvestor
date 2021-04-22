

function isinCellRenderer(params) {
    return '<a href="/chart?isin=' + params.value + '" target="_blank">'+ params.value + '</a>'
}

function grid(toElementId, gridOptions) {
    // lookup the container we want the Grid to use
    var eGridDiv = document.querySelector('#' + toElementId);
    gridOptions["components"] = {"isinCellRenderer": isinCellRenderer}

    // create the grid passing in the div to use together with the columns & data we want to use
    new agGrid.Grid(eGridDiv, gridOptions);
};
