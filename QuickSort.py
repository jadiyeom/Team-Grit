import manim

class QuickSortAnimation(Scene):
    def construct(self):
        print("Enter the number of terms")
        nums = int(input("Number of terms: "))
        block_size = 14/nums
        print("Enter the numbers separated by space")
        nums_list = list(map(int, input().split()))
        square_text_pairs = [
            (Square(fill_color=BLUE, fill_opacity=0.5, side_length=block_size*0.7, color=BLUE), Text(str(num), color=WHITE, font_size=9*block_size))
            for num in nums_list
        ]



        square_text_groups = [VGroup(square, text) for square, text in square_text_pairs]

        for i, (square, text) in enumerate(square_text_pairs):
            square.move_to([-7+block_size*(i+1/2), 0, 0])
            text.move_to(square)

        title = Text("Quick Sort", color=WHITE, font_size=30)
        title.move_to([0, 2, 0])

        self.play(Write(title))
        self.play(*[Create(group) for group in square_text_groups])

        for i, (square, text) in enumerate(square_text_pairs):
            new_position = [ -7+block_size*(i+1/2) , 0, 0]
            square_text_groups[i].move_to(new_position)

        self.QuickSort( nums_list, nums-1, 0 ,square_text_groups, block_size)
        for square, text in square_text_groups:
            self.play(square.animate.set_color(GREEN), run_time=0.2)
            self.wait(0.2)
        self.play(FadeOut(title), *[FadeOut(group) for group in square_text_groups])

    def pivotIndex(self, nums_list, high, low ,square_text_groups, block_size):
        pivotIndex = high
        selectionIndex = low
        self.play(square_text_groups[pivotIndex][0].animate.set_color(YELLOW),
                      run_time=0.5)
        for i in range( low, high):
            self.play(square_text_groups[i][0].animate.set_color(RED),
                      square_text_groups[selectionIndex][0].animate.set_color(RED),
                      run_time=0.5)
            self.wait(0.5)
            if nums_list[i] < nums_list[pivotIndex]:
               nums_list[i], nums_list[selectionIndex] = nums_list[selectionIndex], nums_list[i]
               square_text_groups[i], square_text_groups[selectionIndex] = square_text_groups[selectionIndex], square_text_groups[i]
               self.play(
                        square_text_groups[i][0].animate.move_to(square_text_groups[selectionIndex][0].get_center()),
                        square_text_groups[selectionIndex][0].animate.move_to(square_text_groups[i][0].get_center()),
                        square_text_groups[i][1].animate.move_to(square_text_groups[selectionIndex][1].get_center()),
                        square_text_groups[selectionIndex][1].animate.move_to(square_text_groups[i][1].get_center()),
                        run_time=0.5
                    )
               self.play(square_text_groups[selectionIndex][0].animate.set_color(BLUE),
                         run_time=0.5)
               selectionIndex = selectionIndex + 1

            self.play(square_text_groups[i][0].animate.set_color(BLUE),
                      run_time=0.5)
            for k, (square, text) in enumerate(square_text_groups):
                new_position = [-7+block_size*(k+1/2), 0, 0]
                square_text_groups[k].move_to(new_position)

        self.play(square_text_groups[selectionIndex][0].animate.set_color(RED),
                         run_time=0.5)
        nums_list[pivotIndex], nums_list[selectionIndex] = nums_list[selectionIndex], nums_list[pivotIndex]
        square_text_groups[pivotIndex], square_text_groups[selectionIndex] = square_text_groups[selectionIndex], square_text_groups[pivotIndex]
        self.play(
                        square_text_groups[pivotIndex][0].animate.move_to(square_text_groups[selectionIndex][0].get_center()),
                        square_text_groups[selectionIndex][0].animate.move_to(square_text_groups[pivotIndex][0].get_center()),
                        square_text_groups[pivotIndex][1].animate.move_to(square_text_groups[selectionIndex][1].get_center()),
                        square_text_groups[selectionIndex][1].animate.move_to(square_text_groups[pivotIndex][1].get_center()),
                        run_time=0.5
                    )
        # for square, text in square_text_groups:
        #     self.play(square.animate.set_color(BLUE), run_time=0.2)
        #     self.wait(0.2)
        self.play(square_text_groups[pivotIndex][0].animate.set_color(BLUE),
                  square_text_groups[selectionIndex][0].animate.set_color(GREEN),
                      run_time=0.5)
        return selectionIndex

    def QuickSort(self, nums_list, high, low ,square_text_groups, block_size):
        if high > low :
             index = self.pivotIndex( nums_list, high, low ,square_text_groups, block_size)
             self.QuickSort(nums_list, index-1, low ,square_text_groups, block_size)
             self.QuickSort(nums_list, high, index+1 ,square_text_groups, block_size)
