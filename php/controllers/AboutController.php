<?php
class AboutController extends Controller
{
    public function aboutAction() {
        $this->setTitle('About');
        $this->render('about.html.php');
    }
}
