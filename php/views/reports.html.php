    <div class="hero-unit">
      <h1>Reports</h1>
      <p>The reports and edits that are currently pending.</p>
    </div>

    <div class="row">
      <div class="span12">
        <h2>Reports</h2>
        <?php
        foreach($values['reportErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>Report #</th>
              <th class="hidden-phone">Username</th>
              <th>Question #</th>
              <th>Question</th>
              <th>Report Text</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['reportResult'] as $res) {
              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td class="hidden-phone">' . $res['username'] . '</td>';
              echo '<td>' . $res['question_num'] . '</td>';
              echo '<td class="breakable">' . $res['original'] . '</td>';
              echo '<td class="breakable">' . $res['report_text'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($values['reportPage'], $values['reportResultCount'], $values['maxResults'], 'rp'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>


    <div class="row">
      <div class="span12">
        <h2>Edits</h2>
        <?php
        foreach($values['editErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>Edit #</th>
              <th class="hidden-phone">Username</th>
              <th>New Question</th>
              <th>Old Question</th>
              <th>Question #</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['editResult'] as $res) {
              $isItalic = false;
              $splitNew = explode('*', $res['question']);
              $splitOld = explode('*', $res['original']);

              $differenceString = '';
              for($y=0;$y<sizeof($splitNew);$y++){
                if($y>0) {
                  $isItalic = false;
                  $differenceString .= '</u>';
                  $differenceString .= '*';
                }
                $brokenNew = str_split($splitNew[$y]);
                if(!array_key_exists($y, $splitOld)){
                  $splitOld[$y] = '*';
                }
                $brokenOld = str_split($splitOld[$y]);
                for($i=0;$i<sizeof($brokenNew);$i++) {
                  if(!array_key_exists($i, $brokenOld)||!array_key_exists($i, $brokenNew)) {
                    if($isItalic==false){
                      $isItalic = true;
                      $differenceString .= '<u>';
                    }
                  } else if($brokenNew[$i]=='*') {
                    $isItalic = false;
                    $differenceString .= '</u>';
                  } else if($brokenNew[$i]!=$brokenOld[$i]) {
                    if($isItalic==false){
                      $isItalic = true;
                      $differenceString .= '<u>';
                    }
                  } else if($brokenNew[$i]==$brokenOld[$i]&&$isItalic==true) {
                    $isItalic = false;
                    $differenceString .= '</u>';
                  }
                  $differenceString.=$brokenNew[$i];
                }
              }
              if($isItalic==true) {
                $differenceString .= '</u>';
              }

              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td class="hidden-phone">' . $res['username'] . '</td>';
              echo '<td class="breakable">' . $differenceString . '</td>';
              echo '<td class="breakable">' . $res['original'] . '</td>';
              echo '<td>' . $res['question_id'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($values['editPage'], $values['editResultCount'], $values['maxResults'], 'ep'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>

    <div class="row">
      <div class="span12">
        <h2>Added Questions</h2>
        <?php
        foreach($values['newErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Author</th>
              <th>New Question</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['newResult'] as $res) {
              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td>' . $res['username'] . '</td>';
              echo '<td class="breakable">' . $res['question'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($values['newPage'], $values['newResultCount'], $values['maxResults'], 'np'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>

    <div class="row">
      <div class="span12">
        <h2>Pending Deletions</h2>
        <?php
        foreach($values['deleteErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>#</th>
              <th class="hidden-phone">Username</th>
              <th>New Question</th>
              <th>Question #</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['deleteResult'] as $res) {
              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td class="hidden-phone">' . $res['username'] . '</td>';
              echo '<td class="breakable">' . $res['question'] . '</td>';
              echo '<td>' . $res['line_num'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($values['deletePage'], $values['deleteResultCount'], $values['maxResults'], 'dp'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>
