import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';


@Component({
    selector: 'app-custom-box',
    templateUrl: './custom-box.component.html',
    imports: [FormsModule],
})
export class CustomBoxComponent {

    private privateMessage: string = 'This is a private message in the custom box component.';
    message: string = 'This is a simple custom box component.';

    buttonOn: boolean = false;

    onButtonToggle(): void {
        this.message = this.buttonOn ? this.privateMessage : 'This is a simple custom box component.';
    }

}