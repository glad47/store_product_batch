// store_product_batch/static/src/js/GlobalHeaderButton.js
odoo.define('store_product_batch.GlobalHeaderButton', function (require) {
    'use strict';

    const { Component } = require('@odoo/owl');
    const { useService } = require('@web/core/utils/hooks');
    const { registry } = require('@web/core/registry');

    class GlobalHeaderButton extends Component {
        setup() {
            this.rpc = useService('rpc');
            this.popup = useService('popup');
        }

        async onClick() {
            const { confirmed } = await this.popup.add({
                title: 'Refresh Batches',
                body: 'Do you want to refresh all batch info?',
                confirmText: 'Yes',
                cancelText: 'No',
            });

            if (confirmed) {
                await this.rpc.query({
                    model: 'store.batch',
                    method: 'action_refresh_batches_info',
                    args: [],
                });

                this.popup.add({
                    title: 'Success',
                    body: 'Batch info refreshed!',
                });
            }
        }
    }

    GlobalHeaderButton.template = 'store_product_batch.GlobalHeaderButton';
    return GlobalHeaderButton;
});

// store_product_batch/static/src/js/GlobalHeaderButton.js (continued)
registry.category('control_panel_buttons').add('store_product_batch_global_button', {
    Component: GlobalHeaderButton,
});

